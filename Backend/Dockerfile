FROM python:3.12-alpine
RUN apk add --no-cache gcc musl-dev libffi-dev libpq
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "gunicorn elixir_db.wsgi:application --bind 0.0.0.0:$PORT"]
