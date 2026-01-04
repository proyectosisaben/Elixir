FROM python:3.11-slim

# Instala dependencias del sistema primero
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE $PORT
CMD ["gunicorn", "elixir_db.wsgi:application", "--bind", "0.0.0.0:$PORT"]
