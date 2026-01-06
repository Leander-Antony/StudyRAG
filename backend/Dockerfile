FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    tesseract-ocr \
    ffmpeg \
    curl \
    sqlite3 \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# KILL FITZ
RUN pip install --upgrade pip && \
    pip uninstall -y fitz || true && \
    rm -rf /usr/local/lib/python3.11/site-packages/fitz && \
    pip install --no-cache-dir PyMuPDF && \
    pip install --no-cache-dir -r requirements.txt && \
    python - <<EOF
import fitz
print("FINAL USING:", fitz.__file__)
EOF

# Copy app code
COPY . .

RUN mkdir -p data/vectors data/history

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
