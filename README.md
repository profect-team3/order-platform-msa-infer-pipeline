# Order Forecast - Inference Pipeline

## 1. 프로젝트 개요

이 프로젝트는 학습된 주문량 예측 모델을 실시간으로 서빙하기 위한 추론 파이프라인입니다. FastAPI를 사용하여 REST API를 제공하며, Docker 컨테이너 환경에서 실행됩니다.

## 2. 주요 기능 및 책임

- **모델 서빙**: 학습된 Chronos 모델을 FastAPI 기반의 REST API로 제공합니다.
- **모델 로드**: 서비스 시작 시, Google Cloud Storage(GCS)에서 최신 버전의 모델 아티팩트를 다운로드하여 메모리에 로드합니다.
- **실시간 예측**: `/predict` 엔드포인트를 통해 최근 주문 데이터를 입력받아, 미래 24시간의 주문량과 매출을 예측하여 반환합니다.
- **데이터 수집**: Kafka Consumer (`kafka_consumer/kafka_consumer.py`)를 통해 실시간으로 발생하는 `order.completed` 이벤트를 수집하여 차후 모델 학습을 위한 데이터로 저장합니다.

## 3. 아키텍처

- **서빙 프레임워크**: FastAPI
- **웹 서버**: Uvicorn
- **배포 환경**: Docker 컨테이너 (Google Compute Engine 등에서 실행)
- **모델 저장소**: Google Cloud Storage (GCS)
- **실시간 데이터 수집**: Apache Kafka

## 4. 설정 및 설치

프로젝트의 의존성은 `pyproject.toml`에 정의되어 있으며, `uv`를 사용하여 설치할 수 있습니다. 전체 서비스는 Docker를 통해 빌드하고 실행하는 것을 권장합니다.

```bash
# Docker 이미지 빌드
docker-compose build

# Docker 컨테이너 실행
docker-compose up
```

## 5. 사용법

### 5.1. 서비스 실행

`docker-compose up` 명령어를 사용하여 서비스를 시작합니다. API 서버는 기본적으로 `http://localhost:9082`에서 실행됩니다.

### 5.2. 예측 API 호출

`/predict` 엔드포인트에 `POST` 요청을 보내 실시간 예측을 수행할 수 있습니다. 요청 본문(body)에는 예측에 필요한 가게 정보와 최근 시계열 데이터(`realDataItemList`)가 포함되어야 합니다.

**Example Request Body:**
```json
{
  "data": [
    {
      "timestamp": "2025-09-20T10:00:00",
      "storeId": "store_001",
      "categoryMain": "음식",
      "categorySub": "한식",
      "categoryItem": "비빔밥",
      "region": "강남구",
      "realOrderQuantity": 10,
      "realSalesRevenue": 100000,
      "dayOfWeek": 5,
      "hour": 10,
      "minOrderAmount": 15000,
      "avgRating": 4.5
    }
    // ... more data items
  ],
  "store_id": "store_001",
  "prediction_length": 24
}
```

## 6. 주요 환경 변수

서비스가 정상적으로 동작하기 위해 다음 환경 변수들이 `.env` 파일에 설정되어야 합니다.

- `GCS_MODEL_BUCKET`: 서빙할 모델이 저장된 GCS 버킷 이름
- `GCS_MODEL_PATH`: GCS 버킷 내 모델 아티팩트의 경로
- `KAFKA_BROKER_URL`: 데이터 수집을 위한 Kafka 브로커 주소