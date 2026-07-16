FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations on startup and launch uvicorn
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
