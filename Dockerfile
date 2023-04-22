FROM python:3.8
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apt-get update && \
    xargs -a packages.txt apt-get install -y
CMD ["gunicorn", "--config", "gunicorn_conf.py", "app:app"]
