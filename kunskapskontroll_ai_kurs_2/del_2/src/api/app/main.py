
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from .settings import settings
from .model_loader import load_model_bundle
from .features_loader import get_features_for_symbol

app = FastAPI(title="StockML MVP API", version="0.1.0")

# Configure logging
root_logger = logging.getLogger()

for handler in root_logger.handlers:
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

root_logger.setLevel(logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)

#Fetch correct logger
logger = logging.getLogger(__name__)


class PredictResponse(BaseModel):
    symbol: str
    horizon_days: int
    predicted_return: float
    lower_return: float
    upper_return: float
    confidence: float
    model_version: str | None = None
    generated_at: str
    current_price: float


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

    logger.info(f"Starting prediction for symbol: {s}, horizon: {horizon}, confidence: {confidence}")

    try:        
        _, mapie = load_model_bundle()        
        X = get_features_for_symbol(s)
        
        logger.info(f"Features for symbol {s}: {X.shape[0]} samples")
        
        # Extract current price
        current_price = float(X["current_price"].iloc[0])
        
        alpha = 1.0 - confidence
        y_pred, y_pis = mapie.predict(X.values, alpha=alpha)
        
        # MAPIE returns prediction intervals; shape differs by version. Handle common shape.
        # Expect y_pis: (n_samples, 2, n_alpha)
        lower = float(y_pis[0, 0, 0])
        upper = float(y_pis[0, 1, 0])
        
        logger.info(f"Prediction results for symbol {s}: predicted_return={y_pred[0]}, lower_return={lower}, upper_return={upper}")

        return PredictResponse(
            symbol=s,
            horizon_days=horizon,
            predicted_return=float(y_pred[0]),
            lower_return=lower,
            upper_return=upper,
            confidence=confidence,
            model_version=None,
            generated_at=datetime.now(timezone.utc).isoformat(),
            current_price=current_price
        )
    except Exception as e:
        logger.error(f"Error occurred while making prediction for symbol {s}: {e}")
        raise HTTPException(status_code=500, detail=str(e))    
    
