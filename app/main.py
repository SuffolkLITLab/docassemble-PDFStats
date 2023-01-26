from flask import Flask, redirect, url_for

app = Flask(__name__)

with app.app_context():
    from docassemble.PDFStats.pdfstats import view_stats, UPLOAD_FOLDER, bp
    app.register_blueprint(bp)
    app.config.from_prefixed_env()

@app.route("/")
def hello():
    return redirect(url_for("pdfstats.upload_file"))

if __name__ == "main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)