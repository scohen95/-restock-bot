# Dockerfile
# Uses the official Playwright image — includes Chromium + all system deps.
# This is the most reliable way to run Playwright on Railway.

FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browsers are pre-installed in the base image.
# If you ever change the playwright version, uncomment this:
# RUN playwright install chromium

# Copy app source
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

CMD ["python", "main.py"]
