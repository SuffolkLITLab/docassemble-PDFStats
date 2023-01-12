FROM tiangolo/uwsgi-nginx-flask:python3.11

# RUN pip install opencv-python-headless
RUN apt-get update && apt-get install libgl1 -y
RUN pip install git+https://github.com/SuffolkLITLab/FormFyxer.git@misc_pdfstats

COPY . /docassemble
WORKDIR /docassemble
RUN pip install --editable .

WORKDIR /
COPY ./app /app