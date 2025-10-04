FROM python:3.11-slim

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

RUN pip install --no-cache-dir sentinelhub
RUN pip install --no-cache-dir python-dotenv
RUN pip install --no-cache-dir rasterio
RUN pip install --no-cache-dir numpy

COPY main.py /app/main.py
COPY .env /app/.env

WORKDIR /app
VOLUME ["/app/pulled_data"]
VOLUME ["/app/formatted_data"]
ENTRYPOINT ["python", "main.py"]