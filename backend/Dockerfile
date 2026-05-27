FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# We also need to install gunicorn for production
RUN pip install gunicorn

COPY . .

# Run the application using the PORT environment variable (defaults to 7860 for Hugging Face)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}
