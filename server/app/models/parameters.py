from pydantic import BaseModel
from typing import List, Dict, Optional


class PredictionRequest(BaseModel):
    days: int
    column: str    

class ForecastResponse(BaseModel):
    predictions: List[Dict]
    causes: Dict
    train: List[Dict]
    test: List[Dict]
    
class DropdownItem(BaseModel):
    value: str
    label: str