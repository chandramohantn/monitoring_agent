# ---------- Stage 1: Build dependencies ----------
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build tools (only in builder stage)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip tooling
RUN pip install --upgrade pip setuptools wheel

# Install dependencies into a custom prefix
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ---------- Stage 2: Runtime image ----------
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy your application code
COPY app.py .

# Default command
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "2"]