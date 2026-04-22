FROM python:3.11-slim

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything (templates, static, backend code)
COPY backend/ ./backend/
COPY templates/ ./templates/
COPY static/ ./static/

WORKDIR /app/backend

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120
