# pre-load

from docassemble.webapp.app_object import app, csrf
from docassemble.base.util import path_and_mimetype
import json

import os
from flask import flash, request, redirect, url_for, render_template_string, Markup
from werkzeug.utils import secure_filename
import formfyxer
import textstat

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'pdf'}

# @app.route('/pdfstats', methods=['GET', 'POST'])
# def pdfstats():
#     return "Hello, World"

app.config['PDFSTAT_UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    return '''
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
    body {
        padding-top: 40px;
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
        <label for="formFileLg" class="form-label">PDF file</label>
        <input class="form-control form-control-lg" id="file" name="file" type="file">
    </div>    

        <button type="submit" class="btn btn-primary mb-3">Upload file</button>
  </form>
</main>
</body>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js" integrity="sha384-u1OknCvxWvY5kfmNBILK2hRnQC3Pr17a+RTT6rIHI7NnikvbZlHgTPOOmMi466C8" crossorigin="anonymous"></script>
</html>
    '''

from flask import send_from_directory

@app.route('/pdfstats/view/<name>')
def view_stats(name):
    if not (name and allowed_file(name)):
        raise Exception("Not a valid filename")
    path_to_file = os.path.join(
        app.config["PDFSTAT_UPLOAD_FOLDER"],
        secure_filename(name),
    )
    stats = formfyxer.parse_form(path_to_file, normalize=True, use_spot=False)
    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>File statistics for { name }</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-iYQeCzEYFbKjA/T2uDLTpkwGzCiq6soy8tYaI1GyVh/UjpbCx/TYkiZhlZB6+fzT" crossorigin="anonymous">
    <style>
    .suffolk-blue {{
        background-color: #002e60;
    }}
    body {{
        padding-top: 40px;
    }}
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

<main style="max-width: 500px; margin: auto;">
<h1 class="pb-2 border-bottom">File statistics for { name }</h1>
<table class="table">
    <thead>
    <tr>
      <th scope="col">Statistic name</th>
      <th scope="col">Value</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <th scope="row">
    Consensus reading grade level
    </th>
    <td>{ stats.get("reading grade level") }</td>
    </tr>
    <tr>
    <th scope="row">
    Number of pages
    </th>
    <td>{ stats.get("pages") }</td>
    </tr>
    <tr>
    <th scope="row">
    Number of fields
    </th>
    <td>{ len(stats.get("fields",[])) }</td>
    </tr>
    <tr>
    <th scope="row">
    Average number of fields per page
    </th>
    <td>{ stats.get("avg fields per page") }</td>
    </tr>
    <tr>
    <th scope="row">
    Word count
    </th>
    <td>{ len(stats.get("text").split(" ")) }</td>
    </tr>
    <tr>
    <th scope="row">
    Number of "difficult words" (includes inflections of some "easy" words)
    </th>
    <td>{ textstat.difficult_words(stats.get("text")) }</td>
    </tr>    
    </tbody>
</table>
<div class="accordion" id="fullTextAccordion">
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
</div>
</main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js" integrity="sha384-u1OknCvxWvY5kfmNBILK2hRnQC3Pr17a+RTT6rIHI7NnikvbZlHgTPOOmMi466C8" crossorigin="anonymous"></script>
</body>

</html>
    """

#def download_file(name):
#    return send_from_directory(app.config["PDFSTAT_UPLOAD_FOLDER"], name)

app.add_url_rule(
    "/pdfstats/view/<name>", endpoint="view_stats", build_only=True
)