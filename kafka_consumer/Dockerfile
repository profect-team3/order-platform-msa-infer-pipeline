FROM python:3.11-slim

WORKDIR /app

COPY kafka_consumer/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY kafka_consumer/ ./kafka_consumer/

CMD ["python", "-u", "kafka_consumer/kafka_consumer.py"]
