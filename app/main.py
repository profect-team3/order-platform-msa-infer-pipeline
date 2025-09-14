from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from autogluon.timeseries import TimeSeriesPredictor
import os
import mlflow
from mlflow.artifacts import download_artifacts
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Order Platform Forecasting API", version="1.0.0")

MODEL_URI = os.getenv("MODEL_URI")


predictor = None

def load_predictor() -> None:
    global predictor
    uri = MODEL_URI

    try:
        predictor = TimeSeriesPredictor.load(uri)
    except Exception as e:
        print(f"Error loading predictor from {uri}: {e}")
        predictor = None

class PredictionRequest(BaseModel):
    store_id: str = "store_001"
    prediction_length: int = 24
    data: list[dict] | None = None  # Optional: list of data records (e.g., from CSV)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    load_predictor()
    return {"ready": predictor is not None, "model_uri": MODEL_URI}


@app.post("/predict")
async def predict(request: PredictionRequest):
    if predictor is None:
        return {"error": f"Model not loaded from {MODEL_PATH}"}
    ts_df = pd.DataFrame(request.data)

    predictions = predictor.predict(ts_df)

    result = predictions.reset_index()

    return {
        "store_id": request.store_id,
        "predictions": result[["timestamp", "pred_sales_revenue", "pred_order_quantity"]].to_dict("records"),
        "prediction_length": request.prediction_length,
        "timestamp": pd.Timestamp.now().isoformat(),
    }