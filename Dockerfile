FROM python:3.11-slim

WORKDIR /app

# Install system dependencies that pandas or other packages might need
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY src/ /app/src/

EXPOSE 8080

CMD ["python", "src/__main__.py"]
