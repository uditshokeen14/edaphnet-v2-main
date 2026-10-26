# Multi-Platform Production Dockerfile for EdaphNet v2
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8001

WORKDIR /app

# Install minimal OS runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-deploy.txt ./
# Install PyTorch CPU wheels specifically to keep Docker image size small (~200MB vs 2GB GPU wheels)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements-deploy.txt

# Copy application source code and models
COPY . /app

EXPOSE 8001 8501

# Entrypoint script: supports both native server and streamlit
# To run Streamlit: set env var APP_MODE=streamlit
CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"streamlit\" ]; then streamlit run streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0; else python app/server.py --port=${PORT:-8001} --host=0.0.0.0; fi"]
