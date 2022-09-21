# pre-load


from docassemble.webapp.app_object import app, csrf

import os
from flask import flash, request, redirect, url_for, render_template_string, Markup
from werkzeug.utils import secure_filename
import formfyxer

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
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

from flask import send_from_directory

@app.route('/pdfstats/view/<name>')
def download_file(name):
    return send_from_directory(app.config["PDFSTAT_UPLOAD_FOLDER"], name)

app.add_url_rule(
    "/pdfstats/view/<name>", endpoint="view_stats", build_only=True
)