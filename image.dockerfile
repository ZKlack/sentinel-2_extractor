FROM python:3.11-slim

RUN pip install --no-cache-dir sentinelhub

ENTRYPOINT ["python", "main.py"]