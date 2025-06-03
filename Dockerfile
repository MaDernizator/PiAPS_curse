# Dockerfile

FROM python:3.12-slim

# Системные зависимости
RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной проект
COPY . .

# Переменные окружения
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Порт, если Flask запускается без Gunicorn
EXPOSE 5000

CMD ["flask", "run"]
