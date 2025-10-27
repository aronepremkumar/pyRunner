# Use slim Python image to keep it small
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    gcc \
    make \
    git \
    # Try to install nsjail from the package repository if available
    nsjail || true
# If nsjail not available via apt, try fetching prebuilt binary (best-effort).
# NOTE: If this wget fails because a release doesn't exist, build may still succeed if `nsjail` was installed by apt above.
RUN if [ ! -f /usr/sbin/nsjail ]; then \
      echo "Attempting to download nsjail binary from github releases..."; \
      wget -q -O /usr/sbin/nsjail https://github.com/google/nsjail/releases/latest/download/nsjail || true; \
      chmod +x /usr/sbin/nsjail || true; \
    fi
# Create app directory
WORKDIR /app
# Copy app
COPY app.py /app/app.py
# Install python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# Expose 8080 (Cloud Run expects PORT env or 8080)
ENV PORT=8080
EXPOSE 8080
# Use a non-root user for running the Flask app
RUN groupadd -r app && useradd -r -g app app
USER app
# Run the Flask app via gunicorn for production-like runtime; keep simple here
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--workers", "1", "--threads", "8"]
