FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV DATABASE_URL=postgresql://skystream_user:skystream_password@db:5432/skystream_db

EXPOSE 5000

CMD ["python", "app.py"]