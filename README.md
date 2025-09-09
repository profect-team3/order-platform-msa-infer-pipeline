# Order Platform MSA Infer Pipeline

FastAPI 기반 추론(서빙) 서비스입니다. `uv`로 의존성을 관리하며 AutoGluon TimeSeriesPredictor로 시계열 예측을 제공합니다.

## 요구사항
- Python 3.11+
- uv 설치: https://docs.astral.sh/uv/

## 설치
```bash
uv sync
```

## 로컬 실행
```bash
export MODEL_PATH=models/latest
export DATA_PATH=data/serving_train_finetuned.csv
uv run uvicorn app.main:app --host 0.0.0.0 --port 9082
```

### MLflow 모델 레지스트리 연동
다음 중 하나로 모델을 지정할 수 있습니다(우선순위 상단일수록 우선 적용):

1) 명시적 MLflow 모델 URI 지정
```bash
export MODEL_URI="models:/order-forecast/Production"   # 또는 runs:/<run_id>/artifacts/model
```

2) 모델 등록명 + 스테이지 지정
```bash
export MLFLOW_TRACKING_URI=http://localhost:8001
export MLFLOW_MODEL_NAME=order-forecast
export MLFLOW_MODEL_STAGE=Production   # (기본값: Production)
```

3) 로컬 디렉토리 경로 (기본값)
```bash
export MODEL_PATH=models/latest
```

## Docker
```bash
docker build -t order-platform-msa-infer .

docker run -p 9082:9082 \
  -e MODEL_PATH=models/latest \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:8001 \
  -e MLFLOW_MODEL_NAME=order-forecast \
  -e MLFLOW_MODEL_STAGE=Production \
  -e DATA_PATH=data/serving_train_finetuned.csv \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  order-platform-msa-infer
```

## Docker Compose
```bash
docker-compose up --build
```

## API
- GET /health: 헬스 체크
- GET /ready: 모델 로딩 상태 확인
- POST /predict: 예측 수행

### 요청 예시
```json
{
  "store_id": "store_001",
  "prediction_length": 24
}
```

### 응답 예시
```json
{
  "store_id": "store_001",
  "predictions": [
    {"timestamp": "2024-09-09T00:00:00Z", "mean": 12.3}
  ],
  "prediction_length": 24,
  "timestamp": "2024-09-09T12:34:56.789Z"
}
```

## 참고
- `MODEL_PATH`는 AutoGluon `TimeSeriesPredictor.load()`가 읽을 수 있는 디렉터리여야 합니다.
- `DATA_PATH`는 `pandas.read_csv`로 읽을 수 있는 파일이어야 하며, 서비스 예시는 동일 스키마의 피처링된 학습 데이터로부터 예측을 수행합니다.
