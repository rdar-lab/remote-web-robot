FROM tiangolo/uwsgi-nginx-flask:python3.9-2021-10-26

RUN apt-get update
RUN apt-get install -y firefox-esr

COPY requirements.txt /app/requirements.txt
# Do not use pip-sync here as it removes uwsgi
RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt
COPY /app.py /app/app.py
COPY uwsgi.ini /app/uwsgi.ini
COPY nginx.conf /app/nginx.conf

