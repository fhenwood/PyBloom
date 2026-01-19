FROM python:3.11-slim

# Install system dependencies for BLE
RUN apt-get update && apt-get install -y \
    bluetooth \
    bluez \
    libbluetooth-dev \
    libdbus-1-dev \
    libglib2.0-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package and MQTT dependencies
RUN pip install -e . && \
    pip install aiomqtt

# Create non-root user
RUN useradd -m -s /bin/bash xbloom
USER xbloom

# Expose MQTT client (no specific ports needed)
EXPOSE 1883

# Default command
CMD ["xbloom", "bridge", "--help"]