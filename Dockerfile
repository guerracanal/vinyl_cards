FROM python:3.8-slim-buster
COPY . /app
WORKDIR /app
RUN apt-get update && \
    xargs -a packages.txt apt-get install -y
RUN pip install -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "5", "--threads", "3", "webapp:app"]
