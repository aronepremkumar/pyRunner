# Use slim Python image
FROM python:3.11-slim AS builder

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    pkg-config \
    autoconf \
    automake \
    libtool \
    bison \
    flex \
    protobuf-compiler \
    libprotobuf-dev \
    libnl-route-3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build nsjail from source
RUN git clone https://github.com/google/nsjail.git /tmp/nsjail && \
    cd /tmp/nsjail && make && \
    cp nsjail /usr/sbin/nsjail

# Set working directory
WORKDIR /app

# Copy app files
COPY requirements.txt app.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a writable tmp folder
RUN mkdir -p /app/tmp && chmod 777 /app/tmp

# Expose Cloud Run port
ENV PORT=8080
EXPOSE 8080

# Use non-root user for Cloud Run security
RUN groupadd -r app && useradd -r -g app app
USER app

# Run Flask with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
