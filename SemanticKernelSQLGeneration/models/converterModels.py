# models/converterModels.py
from pydantic import BaseModel, ConfigDict, Field, field_validator, validator
from typing import Dict, Optional

class LampConnections(BaseModel):
    min: float
    max: float
    
    @field_validator('min', 'max', mode='before')
    def convert_values(cls, v):
        v_str = str(v)
        # Handle comma decimals
        v_str = v_str.replace(',', '.')
        return float(v_str)


class VoltageRange(BaseModel):
    min: float
    max: float

    @field_validator('min', 'max', mode='before')
    def convert_values(cls, v):
        v_str = str(v)
        # Handle comma decimals
        v_str = v_str.replace(',', '.')
        return float(v_str)

    
class PowerConverter(BaseModel):
    doc_id: Optional[str] = Field(None, alias="id")
    artnr: Optional[int] = Field(None, alias="artnr")
    ip_rating: Optional[int] = Field(None, alias="ip")
    lamps: Optional[Dict[str, LampConnections]] = Field(default_factory=dict, alias="lamps")  
    
    type: Optional[str] = Field(None, alias="type")  
    name: Optional[str] = Field(None, alias="name")  
    efficiency: Optional[float] = Field(None, alias="efficiency_full_load")
    pdf_link: Optional[str] = Field(None, alias="pdf_link")
    converter_description: Optional[str] = Field(None, alias="converter_description")

    nom_input_voltage: Optional[VoltageRange] = Field(None, alias="nom_input_voltage_v")
    output_voltage:Optional[VoltageRange]= Field(None, alias="output_voltage_v")

    unit: Optional[str] = Field(None, alias="unit")
    price: Optional[float] = Field(None, alias="listprice")
    life_cycle: Optional[str] = Field(None, alias="lifecycle")
    size: Optional[str] = Field(None, alias="size")
    ccr_amplitude: Optional[str] = Field(None, alias="ccr_amplitude")
    dimmability: Optional[str] = Field(None, alias="dimmability")
    dim_list_type: Optional[str] = Field(None, alias="dimlist_type")

    strain_relief: Optional[str] = Field(None, alias="strain_relief")
    gross_weight: Optional[float] = Field(None, alias="gross_weight")

    similarity_score: Optional[float] = Field(None, alias="SimilarityScore")  # For hybrid search results
    model_config = ConfigDict(
        populate_by_name=True,  # Critical fix

        extra="ignore"  
    )