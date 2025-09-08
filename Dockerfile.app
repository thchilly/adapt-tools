FROM python:3.11-slim

# System deps 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

ARG APP_VERSION=0.0.0-dev
ARG GIT_SHA=unknown

# OCI image labels (nice to have)
LABEL org.opencontainers.image.version="$APP_VERSION" \
      org.opencontainers.image.revision="$GIT_SHA"

# Make them available at runtime
ENV APP_VERSION="$APP_VERSION" \
    GIT_SHA="$GIT_SHA"

    
# Unprivileged user for running the app
RUN useradd -m -u 1001 appuser

# Working directory
WORKDIR /app

# Install Python deps first for layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy code (compose also mounts it read-only; this copy is a fallback)
COPY app /app/app
COPY public /app/public
RUN chown -R appuser:appuser /app

# Drop privileges
USER appuser

# Streamlit settings to run in container
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501
CMD ["streamlit", "run", "app/app.py"]