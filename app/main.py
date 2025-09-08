from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from autogluon.timeseries import TimeSeriesPredictor
import mlflow
app = FastAPI(title="Order Platform Forecasting API", version="1.0.0")

# predictor.pkl 경로, 데이터 경로 설정
MODEL_PATH = "models/ag-20250908_122452"
DATA_PATH = "data/serving_train_finetuned.csv"

# MLFLOW_TRACKING_URI = "http://localhost:5000"

# # MLflow 설정
# mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

predictor = TimeSeriesPredictor.load(MODEL_PATH)

# 요청 데이터 모델
class PredictionRequest(BaseModel):
    store_id: str = "store_001"
    prediction_length: int = 24
    fine_tune: bool = True
    # include_covariates: bool = True
    # covariates_data: dict = None  # 예: {"category": "cake", "region": "Yeoksam", ...}

@app.post("/predict")
async def predict(request: PredictionRequest):
    ts_df = pd.read_csv(DATA_PATH)
    
    predictions = predictor.predict(ts_df, model='ChronosFineTuned[bolt_small]')

    result = predictions.reset_index()
    result = result[result['item_id'] == request.store_id]
    
    return {
        "store_id": request.store_id,
        "predictions": result[['timestamp', 'mean']].to_dict('records'),
        "prediction_length": request.prediction_length,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=9082, reload=True, timeout_keep_alive=300)
