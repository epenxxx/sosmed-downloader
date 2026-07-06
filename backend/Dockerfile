FROM python:3.10-slim

# Install FFmpeg dan Driver iGPU AMD (VA-API)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libva2 \
    mesa-va-drivers \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

# Jalankan server FastAPI di port 3333
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3333"]
