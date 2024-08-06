from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class PredictionRequest(BaseModel):
    column: str
    days: Optional[int] = Field(default=1, description="Number of days for prediction, default is 1 if not provided")
    

class ForecastResponse(BaseModel):
    predictions: List[Dict]
    causes: Dict
    train: List[Dict]
    test: List[Dict]
    
class DropdownItem(BaseModel):
    value: str
    label: str