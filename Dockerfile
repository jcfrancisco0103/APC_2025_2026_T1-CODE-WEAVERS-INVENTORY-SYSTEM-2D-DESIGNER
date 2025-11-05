# Multi-stage build for optimized Docker image
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim as production

# Set working directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy project files (excluding unnecessary files via .dockerignore)
COPY . /app/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Copy entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use entrypoint to run migrations, collectstatic, then start gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
