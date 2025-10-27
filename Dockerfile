# Use slim Python image to keep it small
FROM debian:bookworm-slim AS builder

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    protobuf-compiler \
    libprotobuf-dev \
    libnl-route-3-dev \
    libtool \
    autoconf \
    automake \
    bison \
    flex \
    pkg-config \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Clone and build nsjail
RUN git clone https://github.com/google/nsjail.git /tmp/nsjail && \
    cd /tmp/nsjail && make && \
    cp nsjail /usr/local/bin/nsjail


FROM python:3.11-slim

# Create app directory
WORKDIR /app
# Install minimal runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libprotobuf-dev \
    libnl-route-3-dev \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy nsjail binary from builder stage
COPY --from=builder /usr/local/bin/nsjail /usr/sbin/nsjail


# Copy app
COPY requirements.txt app.py ./
RUN pip install --no-cache-dir -r requirements.txt
# Expose 8080 (Cloud Run expects PORT env or 8080)
EXPOSE 8080
ENV PORT=8080
# Use a non-root user for running the Flask app
RUN groupadd -r app && useradd -r -g app app
USER app
# Use Gunicorn as production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]