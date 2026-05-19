
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from .settings import settings
from .model_loader import load_model_bundle
from .features_loader import get_features_for_symbol


# -------- Logging configuration (runs at startup) --------

root_logger = logging.getLogger()

# Update formatter on existing handlers (important for Uvicorn/Azure)
for handler in root_logger.handlers:
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

root_logger.setLevel(logging.INFO)

# Reduce Azure SDK noise
logging.getLogger("azure").setLevel(logging.WARNING)


# Module logger
logger = logging.getLogger(__name__)


app = FastAPI(title="StockML MVP API", version="0.1.0")

class PredictResponse(BaseModel):
    symbol: str
    horizon_days: int
    predicted_return: float
    lower_return: float
    upper_return: float
    predicted_price: float
    lower_price: float
    upper_price: float
    confidence: float
    model_version: str | None = None
    generated_at: str
    recent_price: float


@app.get('/health')
def health():
    return {"status": "ok"}


@app.get('/predict', response_model=PredictResponse)
def predict(symbol: str, horizon: int = 7, confidence: float = 0.90):
    s = symbol.strip().upper()

    if horizon != settings.horizon_days:
        raise HTTPException(status_code=400, detail=f"Only horizon={settings.horizon_days} supported in MVP")

    if s not in settings.symbol_whitelist:
        raise HTTPException(status_code=400, detail=f"Symbol {s} is not in OMX30 whitelist")

    if confidence <= 0.5 or confidence >= 0.99:
        raise HTTPException(status_code=400, detail="confidence must be between 0.50 and 0.99")

    logger.warning(f"Starting prediction for symbol: {s}, horizon: {horizon}, confidence: {confidence}")

    try:
        logger.warning("Calling load_model_bundle()")
        
        _, mapie, feature_cols = load_model_bundle()
        
        feature_cols_str = ", ".join(feature_cols)
        logger.warning(f"Loaded model bundle. Feature columns: {feature_cols_str}")
        
        logger.warning("Finished load_model_bundle()")
        
        logger.warning("Calling get_features_for_symbol()")
        X = get_features_for_symbol(s)
        
        X_str = ", ".join(X.columns)
        logger.warning(f"Loaded features for symbol {s}. Columns: {X_str}")
        
        # Extract recent price
        recent_price = float(X["recent_price"].iloc[0])
        
        X_model = X[feature_cols].values
        
        # interval & prediction
        y_pred, y_pis = mapie.predict_interval(X_model)
        logger.warning(f"Model prediction for symbol {s}: {y_pred[0]}")
        logger.warning(f"Model prediction interval for symbol {s}: {y_pis}")
        logger.warning(f"Model prediction interval shape for symbol {s}: {y_pis.shape}")
        
        pred_return = float(y_pred[0])
        lower_return = float(y_pis[0, 0, 0])
        upper_return = float(y_pis[0, 1, 0])
        logger.warning(f"Prediction interval for symbol {s}: lower={lower_return}, upper={upper_return}")
                
        predicted_price = recent_price * (1 + pred_return)
        lower_price = recent_price * (1 + lower_return)
        upper_price = recent_price * (1 + upper_return)
        logger.warning(f"Predicted price for symbol {s}: {predicted_price}")
        logger.warning(f"Predicted price interval for symbol {s}: lower={lower_price}, upper={upper_price}")

        
        return PredictResponse(
            symbol=s,
            horizon_days=horizon,
            predicted_return=pred_return,
            lower_return=lower_return,
            upper_return=upper_return,            
            predicted_price=predicted_price,
            lower_price=lower_price,
            upper_price=upper_price,
            confidence=confidence,
            model_version=None,
            generated_at=datetime.now(timezone.utc).isoformat(),
            recent_price=recent_price
        )
    except Exception as e:
        logger.error(f"Error occurred while making prediction for symbol {s}: {e}")
        raise HTTPException(status_code=500, detail=str(e))    
    
