FROM python:3.11-slim

# build-essential 설치 (gcc 포함)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv sync

COPY kafka_consumer/ ./kafka_consumer/

CMD ["uv", "run", "python", "-u", "kafka_consumer/kafka_consumer.py"]