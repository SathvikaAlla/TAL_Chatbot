# models/converterModels.py
from pydantic import BaseModel
from typing import Dict, Optional

class LampConnections(BaseModel):
    min: int
    max: int

class PowerConverter(BaseModel):
    artnr: int  # Partition key
    lamps: Optional[Dict[str, LampConnections]]
    name: str
    efficiency: float
    ip_rating: int
    pdf_link: Optional[str] = None
