from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from autogluon.timeseries import TimeSeriesPredictor
import os
import mlflow
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Order Platform Forecasting API", version="1.0.0")

# 환경변수 기반 설정 (기본값 제공)
MODEL_PATH = os.getenv("MODEL_PATH", "models/latest")
DATA_PATH = os.getenv("DATA_PATH", "data/serving_train_finetuned.csv")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME")
MLFLOW_MODEL_STAGE = os.getenv("MLFLOW_MODEL_STAGE", "Production")
MODEL_URI = os.getenv("MODEL_URI")

def resolve_model_uri() -> str | None:
    # 1) explicit MODEL_URI has highest priority
    if MODEL_URI:
        return MODEL_URI

    # 2) MLflow model registry by name+stage
    if MLFLOW_MODEL_NAME:
        return f"models:/{MLFLOW_MODEL_NAME}/{MLFLOW_MODEL_STAGE}"

    # 3) fallback to local directory path
    if MODEL_PATH:
        return MODEL_PATH

    return None


predictor = None

def load_predictor() -> None:
    global predictor
    uri = resolve_model_uri()
    if uri is None:
        return

    try:
        if MLFLOW_TRACKING_URI:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

        if uri.startswith("models:/") or uri.startswith("runs:/"):
            local_path = mlflow.artifacts.download_artifacts(artifact_uri=uri)
        elif uri.startswith("mlflow-artifacts:/"):
            # Parse mlflow-artifacts URI to runs URI
            parts = uri.split("/")
            run_id = parts[1]
            path = "/".join(parts[3:])
            artifact_uri = f"runs:/{run_id}/artifacts/{path}"
            local_path = mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri)
            # TimeSeriesPredictor expects a directory
            local_path = os.path.dirname(local_path)
        else:
            local_path = uri

        if os.path.isdir(local_path):
            predictor = TimeSeriesPredictor.load(local_path)
        else:
            raise FileNotFoundError(f"Model directory not found: {local_path}")
    except Exception as e:
        print(f"Error loading predictor from {uri}: {e}")
        predictor = None


load_predictor()


class PredictionRequest(BaseModel):
    store_id: str = "store_001"
    prediction_length: int = 24


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    return {"ready": predictor is not None, "model_uri": resolve_model_uri()}


@app.post("/predict")
async def predict(request: PredictionRequest):
    if predictor is None:
        return {"error": f"Model not loaded from {MODEL_PATH}"}

    ts_df = pd.read_csv(DATA_PATH)

    predictions = predictor.predict(ts_df)

    result = predictions.reset_index()
    result = result[result['item_id'] == request.store_id]

    return {
        "store_id": request.store_id,
        "predictions": result[["timestamp", "mean"]].to_dict("records"),
        "prediction_length": request.prediction_length,
        "timestamp": pd.Timestamp.now().isoformat(),
    }