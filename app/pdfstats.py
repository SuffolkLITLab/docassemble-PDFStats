import os
import re
import json
from typing import Tuple, Union, List
from hashlib import sha256
import math

import textstat
import pandas
from flask import (
    Blueprint,
    render_template_string,
    request,
    redirect,
    url_for,
    current_app,
    send_from_directory,
)

from werkzeug.utils import secure_filename

import formfyxer
from formfyxer import lit_explorer

import secrets

bp = Blueprint("pdfstats", __name__, url_prefix="/")

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
UPLOAD_FOLDER = "/tmp"
ALLOWED_EXTENSIONS = {"pdf"}

current_app.config["PDFSTAT_UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def valid_uuid(file_id):
    return bool(
        re.match(
            r"^[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}$",
            file_id,
        )
    )


def valid_hash(hash):
    return bool(re.match(r"^[A-Fa-f0-9]{64}$", hash))


def minutes_to_hours(minutes: Union[float, int]) -> str:
    minutes = round(minutes)
    if minutes < 2:
        return "1 minute"
    if minutes > 60:
        res = divmod(minutes, 60)
        return f"{res[0]} hour{'s' if res[0] > 1 else ''} and { res[1] } minute{'s' if res[1] > 1 or res[1] < 1 else ''}"
    else:
        return f"{minutes} minute{'s' if minutes > 1 else ''}"


def highlight_text(text: str, ranges: List[Tuple[int, int]], class_name="highlight"):
    output = []
    prev_end = 0

    for start, end in sorted(ranges):
        output.append(text[prev_end:start])
        output.append(f'<span class="{class_name}">')
        output.append(text[start:end])
        output.append("</span>")
        prev_end = end

    output.append(text[prev_end:])
    return "".join(output)


def get_template_from_static_dir(template_name: str) -> str:
    path = os.path.join(SITE_ROOT, "templates/", template_name)
    with open(path) as f:
        template_str = f.read()
    return template_str


@bp.route("/pdfstats", methods=["GET", "POST"])
def redirect_pdfstats():
    return redirect("/")


@bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_content = file.read()
            intermediate_dir = str(
                sha256(file_content).hexdigest()
            )  # str(uuid.uuid4())
            to_path = os.path.join(
                current_app.config["PDFSTAT_UPLOAD_FOLDER"], intermediate_dir
            )
            if os.path.isdir(to_path):
                if os.path.isfile(os.path.join(to_path, "stats.json")):
                    return redirect(
                        url_for("pdfstats.view_stats", file_hash=intermediate_dir)
                    )
            else:
                os.mkdir(to_path)
            full_path = os.path.join(to_path, filename)
            with open(full_path, "wb") as write_file:
                write_file.write(file_content)
            stats = formfyxer.parse_form(
                full_path,
                normalize=True,
                debug=True,
                openai_creds=current_app.config.get("OPEN_AI"),
                spot_token=current_app.config.get("SPOT_TOKEN"),
                tools_token=current_app.config.get("TOOLS_TOKEN"),
            )
            with open(os.path.join(to_path, "stats.json"), "w") as stats_file:
                stats_file.write(json.dumps(stats))
            return redirect(url_for("pdfstats.view_stats", file_hash=intermediate_dir))
    return render_template_string(get_template_from_static_dir("ratemypdf.html"))


def get_pdf_from_dir(file_hash):
    path_to_dir = os.path.join(
        current_app.config["PDFSTAT_UPLOAD_FOLDER"],
        secure_filename(file_hash),
    )
    for f in os.listdir(path_to_dir):
        if f.endswith(".pdf"):
            return f
    return None


@bp.app_template_filter()
def format_number(number: Union[float, str]):
    return "{:,.2f}".format(float(number))


@bp.route("/download/<file_hash>")
def download_file(file_hash):
    if not (file_hash and valid_hash(file_hash)):
        raise Exception("Not a valid filename")
    f = get_pdf_from_dir(file_hash)
    if f:
        return send_from_directory(
            directory=current_app.config["PDFSTAT_UPLOAD_FOLDER"],
            path=os.path.join(file_hash, f),
        )
    raise Exception("No file uploaded here")


@bp.route("/view/<file_hash>")
def view_stats(file_hash):
    if not (file_hash and valid_hash(file_hash)):
        # allow to upload file again
        return redirect("/")
    to_dir = os.path.join(current_app.config["PDFSTAT_UPLOAD_FOLDER"], file_hash)
    with open(os.path.join(to_dir, "stats.json")) as stats_file:
        stats = json.loads(stats_file.read())
    metric_means = {
        "complexity score": 18.25398487,
        "time to answer": 49.266632,
        "reading grade level": 7.180685,
        "pages": 2.2601246,
        "total fields": 38.38878,
        "avg fields per page": 20.98784,
        "number of sentences": 71.4894,
        "difficult word count": 75.675389408,
        "difficult word percent": 0.127301677,
        "number of passive voice sentences": 8.11557632,
        "sentences per page": 31.25462694,
        "citation count": 1.098442367,
    }
    metric_stddev = {
        "complexity score": 5.86058205587,
        "time to answer": 82.79478559926,
        "reading grade level": 1.561731,
        "pages": 1.97868674,
        "total fields": 47.211886658,
        "avg fields per page": 20.96440214,
        "number of sentences": 83.419848187,
        "difficult word count": 75.67538940809969,
        "difficult word percent": 0.03873129,
        "sentences per page": 14.38664529,
        "number of passive voice sentences": 10.843292156557,
        "citation count": 4.122761536011,
    }

    def percent_of_2_stddev(score, mean, stddev):
        max = mean + (2 * stddev)
        return score / max * 100

    word_count = len(stats.get("text").split(" "))
    if stats.get("number of passive voice sentences") and stats.get(
        "number of sentences"
    ):
        passive_percent = (
            int(stats["number of passive voice sentences"])
            / stats["number of sentences"]
        )
    else:
        passive_percent = 0

    vars = {
        "stats": stats,
        "passive_percent": passive_percent,
        "title": stats.get("title", file_hash),
        "complexity_score": formfyxer.form_complexity(stats),
        "word_count": word_count,
        "word_count_per_page": word_count / float(stats.get("pages") or 1.0),
        "difficult_word_count": textstat.difficult_words(stats.get("text")),
        "metric_means": metric_means,
        "metric_stddev": metric_stddev,
        "percent_of_2_stddev": percent_of_2_stddev,
        "highlight_text": highlight_text,
        "minutes_to_hours": minutes_to_hours,
        "file_hash": file_hash,
        "int": int,
        "float": float,
        "floor": math.floor,
        "round": round,
        "pandas": pandas,
        "lit_explorer": lit_explorer,
    }
    return render_template_string(
        get_template_from_static_dir("ratemypdf_stats.html"),
        **vars,
    )
