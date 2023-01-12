# pre-load

from docassemble.webapp.app_object import app, csrf
from docassemble.base.util import path_and_mimetype, get_config
import json

import os
from flask import flash, request, redirect, url_for, render_template_string, Markup
from werkzeug.utils import secure_filename
import formfyxer
from formfyxer import lit_explorer
import textstat

import pandas

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'pdf'}

# @app.route('/pdfstats', methods=['GET', 'POST'])
# def pdfstats():
#     return "Hello, World"

app.config['PDFSTAT_UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def minutes_to_hours(minutes:float)->str:
  if minutes < 2:
    return "1 minute"
  if minutes > 60:
    res = divmod(minutes, 60)
    return f"{res[0]} hour{'s' if res[0] > 1 else ''} and { res[1] } minute{'s' if res[1] > 1 or res[1] < 1 else ''}"
  else:
    return f"{minutes} minute{'s' if minutes > 1 else ''}"

upload_form = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Upload PDF</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-iYQeCzEYFbKjA/T2uDLTpkwGzCiq6soy8tYaI1GyVh/UjpbCx/TYkiZhlZB6+fzT" crossorigin="anonymous">
    <style>
    .suffolk-blue {
        background-color: #002e60;
    }
    .upload-centered {
        width: 100%;
        max-width: 330px;
        padding: 15px;
        margin: auto;
    }
    </style>
  </head>
<body class="text-center">
<nav class="navbar navbar-dark suffolk-blue">
  <div class="container-fluid">
    <a class="navbar-brand" href="https://suffolklitlab.org">
  <img src="https://apps.suffolklitlab.org/packagestatic/docassemble.MassAccess/lit_logo_light.png?v=0.3.0" alt="Logo" width="30" height="24" class="d-inline-block align-text-top"/>
  Suffolk LIT Lab
  </a>
  </div>
</nav>    
<main class="upload-centered">
    <form method=post enctype=multipart/form-data>
    <h1 class="h3 mb-3 fw-normal">Upload a PDF</h1>

    <div>
        <label for="file" class="form-label">PDF file</label>
        <input class="form-control form-control-md" id="file" name="file" type="file">
    </div>    

        <button type="submit" class="btn btn-primary mb-3 mt-3">Upload file</button>
  </form>
</main>
</body>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js" integrity="sha384-u1OknCvxWvY5kfmNBILK2hRnQC3Pr17a+RTT6rIHI7NnikvbZlHgTPOOmMi466C8" crossorigin="anonymous"></script>
</html>
    '''

@app.route('/pdfstats', methods=['GET', 'POST'])
@csrf.exempt
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['PDFSTAT_UPLOAD_FOLDER'], filename))
            return redirect(url_for('view_stats', name=filename))
    return upload_form

from flask import send_from_directory

@app.route('/pdfstats/view/<filename>')
def view_stats(filename):
    if not (filename and allowed_file(filename)):
        raise Exception("Not a valid filename")
    path_to_file = os.path.join(
        app.config["PDFSTAT_UPLOAD_FOLDER"],
        secure_filename(filename),
    )
    stats = formfyxer.parse_form(path_to_file, normalize=True, debug=True, openai_creds=get_config("open ai"), spot_token=get_config("spot token"))
    title = stats.get('title', filename)
    complexity_score = formfyxer.form_complexity(stats)
    word_count = len(stats.get("text").split(" "))
    difficult_word_count = textstat.difficult_words(stats.get("text"))
    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Stats for { title }</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-iYQeCzEYFbKjA/T2uDLTpkwGzCiq6soy8tYaI1GyVh/UjpbCx/TYkiZhlZB6+fzT" crossorigin="anonymous">
    <style>
    .suffolk-blue {{
        background-color: #002e60;
    }}
    </style>
  </head>
<body>
<nav class="navbar navbar-dark suffolk-blue">
  <div class="container-fluid">
    <a class="navbar-brand" href="https://suffolklitlab.org">
  <img src="https://apps.suffolklitlab.org/packagestatic/docassemble.MassAccess/lit_logo_light.png?v=0.3.0" alt="Logo" width="30" height="24" class="d-inline-block align-text-top"/>
  Suffolk LIT Lab
  </a>
  </div>
</nav>

<main style="max-width: 800px; margin-left: auto; margin-right: auto;">
<h1 class="pb-2 border-bottom text-center">File statistics for <span class="text-break">{ title }</span></h1>
<table class="table text-center">
    <thead>
    <tr>
      <th scope="col">Statistic name</th>
      <th scope="col">Value</th>
      <th scope="col">Note</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <th scope="row">Complexity Score</th>
    <td>{ "{:.2f}".format(complexity_score) }</td>
    <td>Lower is better</td>
    </tr>
    <tr>
    <th scope="row">Time to read</th>
    <td>
    About { minutes_to_hours(int(word_count / 150)) }
    </td>
    <td>Assuming 150 words per minute reading speed.</td>
    </tr>
    <tr>
    <th scope="row">Time to answer</th>
    <td>
    About { minutes_to_hours(round(stats.get("time to answer", (0,0))[0])) }, plus or minus { minutes_to_hours(round(stats.get("time to answer", (0,0))[1])) }
    </td>
    <td>The variation covers 1 standard deviation. See <a href="#flush-collapseThree">the footnotes</a> for more information.</td>
    </tr>
    <tr>
    <th scope="row">
    Consensus reading grade level
    </th>
    <td>Grade { int(stats.get("reading grade level")) }</td>
    <td>Target is <a href="https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/style_guide/readability#target-reading-level">4th-6th grade</a></td>
    </tr>
    <tr>
    <th scope="row">
    Number of pages
    </th>
    <td>{ stats.get("pages") }</td>
    <td></td>
    </tr>
    <tr>
    <th scope="row">
    Number of fields
    </th>
    <td>{ len(stats.get("fields",[])) }</td>
    <td></td>    
    </tr>
    <tr>
    <th scope="row">
    Average number of fields per page
    </th>
    <td>{float(stats.get("avg fields per page",0)):.1f}</td>
    <td>Target is < 15</td>
    </tr>
    <tr>
    <th scope="row">
    Number of sentences
    </th>
    <td>{ stats.get("number of sentences") }</td>
    <td></td>
    </tr>
    <tr>
    <th scope="row">
    Word count / page
    </th>
    <td>{ word_count } ({float(word_count/stats.get("pages",1.0)):.1f})</td>
    <td>Users <a href="https://www.nngroup.com/articles/how-little-do-users-read/">read as little as 20% of the content</a> on a longer page. Try to keep word count to 110 words.</td>
    </tr>
    <tr>
    <th scope="row">
    Number of "difficult words"
    </th>
    <td>{ difficult_word_count } <br/> ({difficult_word_count/word_count * 100:.1f}%)</td>
    <td>May include inflections of some "easy" words. Target is < 5%</td>
    </tr>
    <tr>
    <th scope="row">
    Percent of sentences with passive voice
    </th>
    <td>{stats.get("number of passive voice sentences",0) / stats.get("number of sentences",1) * 100:.1f}%</td>
    <td>Target is < 5%</td>
    </tr>
    <tr>
    <th scope="row">
    Number of citations
    </th>
    <td>{ len(stats.get("citations",[])) }</td>
    <td>Avoid using citations in court forms.</td>
    </tr>
    </tbody>
</table>

<h2 class="pb-2 border-bottom text-center">Ideas for Improvements</h2>

{ "<p>Here's an idea for a new title: <b>" + stats["suggested title"] + "</b></p>" if stats.get("suggested title") else ""}

<p>Here's a idea for an easy-to-read description of the form:
<div class="card text-left">
  <div class="card-body">
   { stats["description"] }
  </div>
</div>
</p>


<div class="accordion text-center" id="fullTextAccordion">
  <div class="accordion-item">
    <h2 class="accordion-header" id="flush-headingOne">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseOne" aria-expanded="false" aria-controls="flush-collapseOne">
        Full text of form
      </button>
    </h2>
    <div id="flush-collapseOne" class="accordion-collapse collapse" aria-labelledby="flush-headingOne" data-bs-parent="#fullTextAccordion">
      <div class="accordion-body">
        { stats.get("text") }
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="flush-headingTwo">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseTwo" aria-expanded="false" aria-controls="flush-collapseTwo">
        Citations
      </button>
    </h2>
    <div id="flush-collapseTwo" class="accordion-collapse collapse" aria-labelledby="flush-headingTwo" data-bs-parent="#fullTextAccordion">
      <div class="accordion-body">
        { "<br/>".join(stats.get("citations",[])) }
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="flush-headingThree">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseThree" aria-expanded="false" aria-controls="flush-collapseThree">
        Information about fields
      </button>
    </h2>
    <div id="flush-collapseThree" class="accordion-collapse collapse" aria-labelledby="flush-headingThree" data-bs-parent="#fullTextAccordion">
      <div class="accordion-body">
      <p><b>Note: "time to answer" is drawn as a random sample from an assumed normal distribution of times to answer, with a pre-set standard deviation and mean that depends
      on the answer type and allowed number of characters. It will likely be a different number if you refresh and recalculate.</b></p>
      { pandas.DataFrame.from_records(stats.get("debug fields")).to_html() if stats.get("debug fields") else [] }
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="flush-headingFour">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseFour" aria-expanded="false" aria-controls="flush-collapseFour">
        Information about complexity
      </button>
    </h2>
    <div id="flush-collapseFour" class="accordion-collapse collapse" aria-labelledby="flush-headingFour" data-bs-parent="#fullTextAccordion">
      <div class="accordion-body">
      <p><b>Note: this is a list of each metric and it's specific score; they are summed together to get the total score</b></p>
      <table class="table">
      <thead>
        <tr>
          <th>Metric name</th>
          <th>Original value</th>
          <th>Weighted value</th>
        </tr>
      </thead>
      <tbody>
        { chr(10).join(['<tr><th scope="row">{}</th><td>{:.2f}</td><td>{:.2f}</td></tr>'.format(v[0], v[1], v[2]) for v in lit_explorer._form_complexity_per_metric(stats)]) }
      </tbody>
      </table>
      </div>
    </div>
  </div>

</div>
<br/>


<a class="btn btn-primary" href="/pdfstats" role="button">Upload a new PDF</a>

</main>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.3/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js" integrity="sha384-u1OknCvxWvY5kfmNBILK2hRnQC3Pr17a+RTT6rIHI7NnikvbZlHgTPOOmMi466C8" crossorigin="anonymous"></script>
    <script>
        $(document).ready(function() {{
            var accordSec = window.location.hash;
            if (accordSec.length) {{
                $(accordSec).collapse("show");
            }}
        }});
    </script>
</body>

</html>
    """

#def download_file(name):
#    return send_from_directory(app.config["PDFSTAT_UPLOAD_FOLDER"], name)

app.add_url_rule(
    "/pdfstats/view/<name>", endpoint="view_stats", build_only=True
)