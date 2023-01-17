FROM tiangolo/uwsgi-nginx-flask:python3.11

# RUN pip install opencv-python-headless
RUN apt-get update && apt-get install libgl1 snapd -y
RUN snap install core; snap refresh core; snap install --classic certbot && ln -s /snap/bin/certbot /usr/bin/certbot
# NOTE: you'll still need to manually run `certbox --nginx` to get the certificates
RUN pip install git+https://github.com/SuffolkLITLab/FormFyxer.git@misc_pdfstats

COPY . /docassemble
WORKDIR /docassemble
RUN pip install --editable .

WORKDIR /
COPY ./app /app