FROM python:3.8-slim-buster
COPY . /app
WORKDIR /app
RUN apt-get update && \
    xargs -a packages.txt apt-get install -y
RUN pip install -r requirements.txt
#CMD ["gunicorn", "--conf", "gunicorn_conf.py", "webapp:app"]
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--conf", "gunicorn_conf.py", "webapp:app"]
