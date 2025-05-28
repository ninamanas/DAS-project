FROM python:3.9-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*


ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:${PATH}"


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY data_ingestion.py .
COPY kafka_reader.py .
COPY data_processor.py .
COPY postgres_writer.py .
COPY spark_streaming_app.py .
COPY schema.json .
COPY analysis_service.py .
COPY config.py .


ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]