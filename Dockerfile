# 빌드 단계
FROM python:3.11-slim AS builder

RUN apt-get update && \
    apt-get install -y build-essential gcc g++ && \
    pip install --no-cache-dir uv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system --no-cache-dir .

# 최종 단계
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y gcc g++ && \
    pip install --no-cache-dir uv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app .
COPY app/ ./app/

EXPOSE 9082

ENV HOST=0.0.0.0 \
    PORT=9082 \
    MODEL_PATH=models/latest \
    DATA_PATH=data/serving_train_finetuned.csv

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9082"]