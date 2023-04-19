FROM python:3.8-slim-buster
COPY . /app
WORKDIR /app
RUN apt-get update && \
    xargs -a packages.txt apt-get install -y
CMD ["gunicorn", "--conf", "gunicorn_conf.py", "webapp:app"]