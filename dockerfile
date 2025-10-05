FROM python:3.11-slim

# disable python output buffering
ENV PYTHONUNBUFFERED=1

# Install system dependencies for rasterio, numpy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libexpat1 \
    libgdal-dev \
    gdal-bin \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python modules
RUN pip install --no-cache-dir sentinelhub
RUN pip install --no-cache-dir python-dotenv
RUN pip install --no-cache-dir rasterio
RUN pip install --no-cache-dir numpy

# Copy application code
COPY main.py /app/main.py

# Define mountable directories
VOLUME ["/app/pulled_data"]
VOLUME ["/app/formatted_data"]

# Set working directory and entrypoint
WORKDIR /app
ENTRYPOINT ["python", "main.py"]