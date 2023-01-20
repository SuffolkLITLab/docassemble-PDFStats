FROM tiangolo/uwsgi-nginx-flask:python3.11

# RUN pip install opencv-python-headless
RUN apt-get update && apt-get install libgl1 python3-pip -y
RUN pip3 install certbot certbot-nginx certbot-dns-route53
# NOTE: manual steps after this: docker exec into container
# `certbot --nginx`, then edit `/etc/nginx/conf.d/nginx.conf` to have `server_name ratemypdf.com`
# then `certbot install --cert-name ratemypdf.com`
RUN pip install git+https://github.com/SuffolkLITLab/FormFyxer.git@tmp_misc_gpt3

COPY . /docassemble
WORKDIR /docassemble
RUN pip install --editable .

WORKDIR /
COPY ./app /app