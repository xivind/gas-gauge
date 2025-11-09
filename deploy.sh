#!/bin/bash

set -o xtrace

# Cleanup container and image
docker container stop gas-gauge
docker container rm gas-gauge
docker image rm gas-gauge

# Build image and tag it
docker build -t gas-gauge .

# Create data directory on host if it doesn't exist
mkdir -p ~/code/container_data

# Create and run container
docker run -d \
  --name=gas-gauge \
  -e TZ=Europe/Stockholm \
  -v ~/code/container_data:/app/data \
  --restart unless-stopped \
  -p 8000:8000 \
  gas-gauge
