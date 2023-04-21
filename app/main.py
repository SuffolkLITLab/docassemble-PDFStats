from flask import Flask, redirect, url_for

app = Flask(__name__)

with app.app_context():
    from pdfstats import bp

    app.register_blueprint(bp)
    app.config.from_prefixed_env()

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=5000)
