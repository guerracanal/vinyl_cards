# Imagen base para Python 3.9
FROM python:3.9-slim-buster

# Instalar paquete con sysctl
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
 && rm -rf /var/lib/apt/lists/*

# Establecer límite de memoria
RUN sysctl -w vm.max_map_count=262144

# Copiar los archivos de la aplicación a la imagen
WORKDIR /app
COPY . /app

# Instalar los paquetes de Nix
RUN apt-get update && apt-get install -y \
    libsm6 libxext6 libgl1-mesa-glx libgl1 libgl1-mesa-dev ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Instalar los requisitos de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8080
#EXPOSE 8080

# Ejecutar el servidor Gunicorn
CMD ["gunicorn", "--config", "gunicorn_conf.py", "app:app"]
