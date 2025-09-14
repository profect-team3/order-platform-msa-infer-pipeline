from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(title="Order Platform Forecasting API", version="1.0.0")

LOCAL_PREDICTOR_PATH = "."


def download_gcs_folder(local_path):
    # gcsfs 또는 google-cloud-storage 사용
    import gcsfs
    fs = gcsfs.GCSFileSystem()
    fs.get('gs://us-central1-mlpipeline-comp-9bf7861c-bucket/model_artifact/1/b193f6501c5d47faba699f403dee68f4/artifacts/predictor/model_artifact', local_path)

predictor = None

def load_predictor(local_path) -> None:
    global predictor
    download_gcs_folder(local_path)
    # predictor = TimeSeriesPredictor.load(local_path)
    predictor = TimeSeriesPredictor.load(local_path, require_version_match=False)


load_predictor('model_artifact')


class RealDataItem(BaseModel):
    timestamp: datetime
    storeId: str
    categoryMain: str
    categorySub: str
    categoryItem: str
    region: str
    realOrderQuantity: int
    realSalesRevenue: int
    dayOfWeek: int
    hour: int
    minOrderAmount: int
    avgRating: int
 

class PredictionRequest(BaseModel):
    data: List[RealDataItem] = Field(..., alias="realDataItemList")
    store_id: str = "store_001"
    prediction_length: int = 24


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    return {"ready": predictor is not None}


@app.post("/predict")
async def predict(request: PredictionRequest):
    if predictor is None:
        return {"error": f"Model not loaded."}
    # print(request)
    df = pd.DataFrame([item.dict() for item in request.data])

    df = df.rename(columns={"storeId": "item_id", "realOrderQuantity": "target"})
    df = df.rename(columns={
    "categoryMain": "category_main",
    "categorySub": "category_sub",
    "categoryItem": "category_item",
    "realSalesRevenue": "real_sales_revenue",
    "dayOfWeek": "day_of_week",
    "minOrderAmount": "min_order_amount",
    "avgRating": "avg_rating"
    })
    
    df = df.sort_values(["item_id", "timestamp"])

    ts_df = TimeSeriesDataFrame.from_data_frame(df, timestamp_column="timestamp", id_column="item_id")
    ts_df = ts_df.convert_frequency(freq='h')
    
    predictions = predictor.predict(ts_df)
    
    result = predictions.reset_index()

    result = result.rename(columns={"mean": "pred_order_quantity"})
    result["pred_order_quantity"] = result["pred_order_quantity"].round().astype(int)
    result["pred_sales_revenue"] = result["pred_order_quantity"]
    
    result["timestamp"] = result["timestamp"].dt.floor('h').dt.strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "store_id": request.store_id,
        "prediction_length": request.prediction_length,
        "predictions": result[["timestamp", "pred_order_quantity", "pred_sales_revenue"]].to_dict("records")
    }
    
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=9082, reload=True, timeout_keep_alive=300)
