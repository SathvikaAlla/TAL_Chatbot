# # models/converterModels.py
# from pydantic import BaseModel
# from typing import Dict, Optional

# class LampConnections(BaseModel):
#     min: int
#     max: int

# class PowerConverter(BaseModel):
#     ARTNR: int  # Partition key
#     lamps: Optional[Dict[str, LampConnections]]
#     name: Optional[str]
#     IP: Optional[int]
#     pdf_link: Optional[str] = None

# models/converterModels.py
from pydantic import BaseModel, ConfigDict, Field, field_validator, validator
from typing import Dict, Optional

class LampConnections(BaseModel):
    min: int
    max: int
    @field_validator('min', 'max', mode='before')
    def convert_strings(cls, v):
        return int(v) if isinstance(v, str) else v

class PowerConverter(BaseModel):
    doc_id: str = Field(..., alias="id")  # Use 'id' as the document ID
    artnr: int = Field(..., alias="ARTNR")  # Map to uppercase ARTNR
    type: Optional[str] = Field(None, alias="TYPE")  # Map to Type
    ip_rating: int = Field(..., alias="IP")  # Map to IP field
    
    lamps: Dict[str, LampConnections] = Field(default_factory=dict, alias="lamps")  # Map to lamps

    @field_validator("lamps", mode="before")
    def parse_lamps(cls, v):
        return {k: LampConnections(**v[k]) for k in v}  # Force parsing
    
    name: Optional[str] = Field(None, alias="Name")  # Map to Name
    efficiency: Optional[float] = Field(None, alias="EFFICIENCY @full load")
    pdf_link: Optional[str] = Field(None, alias="pdf_link")
    converter_description: Optional[str] = Field(None, alias="CONVERTER DESCRIPTION:")
    nom_input_voltage: Optional[str] = Field(None, alias="NOM. INPUT VOLTAGE (V)")
    output_voltage: Optional[str] = Field(None, alias="OUTPUT VOLTAGE (V)")
    unit: Optional[str] = Field(None, alias="Unit")
    price: Optional[float] = Field(None, alias="Listprice")
    life_cycle: Optional[str] = Field(None, alias="LifeCycle")
    size: Optional[str] = Field(None, alias="SIZE: L*B*H (mm)")
    ccr_amplitude: Optional[str] = Field(None, alias="CCR (AMPLITUDE)")
    dimmability: Optional[str] = Field(None, alias="DIMMABILITY")
    dim_list_type: Optional[str] = Field(None, alias="DIMLIST TYPE")

    similarity_score: Optional[float] = Field(None, alias="SimilarityScore")  # For hybrid search results
    model_config = ConfigDict(
        populate_by_name=True,  # Critical fix
        extra="ignore"  
    )