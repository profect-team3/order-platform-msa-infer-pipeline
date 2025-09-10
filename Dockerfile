FROM python:3.11-slim

# install uv via pip (bootstrap only)
RUN pip install --no-cache-dir uv

WORKDIR /app

# copy project metadata first for layer caching
COPY pyproject.toml uv.lock* ./

# install deps with uv
RUN uv sync

# copy app code
COPY app/ ./app/

EXPOSE 9082

ENV HOST=0.0.0.0 \
    PORT=9082 \
    MODEL_PATH=models/latest \
    DATA_PATH=data/serving_train_finetuned.csv

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9082"]


