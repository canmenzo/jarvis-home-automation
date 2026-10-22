FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.1.3 wakeonlan==3.1.0 waitress==3.0.2
COPY app.py .
USER nobody
CMD ["python", "app.py"]
