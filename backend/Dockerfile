FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for OpenCV and YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install python dependencies including Gunicorn and Uvicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn[standard]

COPY . .

EXPOSE 8000

# Start Gunicorn with Uvicorn worker for high-performance ASGI
CMD ["gunicorn", "app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
