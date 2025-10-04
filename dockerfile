FROM python:3.11-slim

RUN pip install --no-cache-dir sentinelhub

COPY main.py /main.py
ENTRYPOINT ["python", "main.py"]