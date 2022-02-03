FROM tiangolo/uwsgi-nginx-flask:python3.9-2021-10-26

RUN apt-get update
RUN apt-get install -y firefox-esr

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz
RUN tar -xvzf geckodriver*
RUN chmod +x geckodriver
RUN cp geckodriver /usr/bin/geckodriver

COPY requirements.txt /app/requirements.txt
# Do not use pip-sync here as it removes uwsgi
RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt
COPY /app.py /app/app.py
COPY uwsgi.ini /app/uwsgi.ini
COPY nginx.conf /app/nginx.conf

