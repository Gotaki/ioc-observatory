FROM python:3.12-slim
WORKDIR /app

# Install dependencies first so Docker caches this layer
COPY collectors/urlhaus/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared schema package, then the collector script
COPY common/ ./common/
COPY collectors/urlhaus/collector.py .

USER nobody
CMD ["python", "collector.py"]