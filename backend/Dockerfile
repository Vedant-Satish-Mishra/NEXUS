FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged user for security
RUN groupadd -g 10001 nexus && useradd -u 10001 -g nexus -m nexus

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY backend /app/backend
COPY contracts /app/contracts
COPY data /app/data

# Ensure data and upload directories exist and permissions are set
RUN mkdir -p /app/data/chroma /app/uploads && \
    chown -R nexus:nexus /app

USER nexus

ENV PYTHONPATH=/app/backend
ENV ENV=prod

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
