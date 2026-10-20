FROM python:3.12-slim
WORKDIR /app
COPY collectors/cisa_kev/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY collectors/cisa_kev/collector.py .
USER nobody
CMD ["python", "collector.py"]
