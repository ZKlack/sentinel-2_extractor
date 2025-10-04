FROM python:3.11-slim

RUN pip install --no-cache-dir sentinelhub
RUN pip install --no-cache-dir python-dotenv

COPY main.py /app/main.py
COPY .env /app/.env

WORKDIR /app
VOLUME ["/app/pulled_data"]
ENTRYPOINT ["python", "main.py"]