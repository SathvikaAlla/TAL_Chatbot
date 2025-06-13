from dataclasses import dataclass
from typing import Dict, List, Optional, Annotated
from pydantic import BaseModel, BeforeValidator, Field, field_validator  # Use Pydantic's Field
from semantic_kernel.data import (
    DistanceFunction,
    IndexKind,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel
)

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

@vectorstoremodel
class PowerConverterVector(BaseModel):
    id: Annotated[str, VectorStoreRecordKeyField]=Field(None, alias="id")
    artnr: Annotated[int, VectorStoreRecordDataField()] = Field(..., alias="artnr")
    ip: Annotated[int, VectorStoreRecordDataField()] = Field(..., alias="ip")
    type: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="type")
    lamps: Optional[Dict[str, LampConnections]] = None

    name: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="name")
    efficiency_full_load: Optional[Annotated[float, VectorStoreRecordDataField()]] = Field(None, alias="efficiency_full_load")
    pdf_link: Optional[Annotated[str, VectorStoreRecordDataField()]] = None
    converter_description: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="converter_description")
    
    nom_input_voltage: Optional[VoltageRange] = Field(None, alias="nom_input_voltage_v")
    output_voltage: Optional[VoltageRange] = Field(None, alias="output_voltage_v")
    
    unit: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="unit")
    price: Optional[Annotated[float, VectorStoreRecordDataField()]] = Field(None, alias="listprice")
    life_cycle: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="lifecycle")
    size: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="size")
    ccr_amplitude: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="ccr_amplitude")
    dimmability: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="dimmability")
    dim_list_type: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="dimlist_type")
    gross_weight: Optional[Annotated[float, VectorStoreRecordDataField()]] = Field(None, alias="gross_weight")
    strain_relief: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="strain_relief")
    embedding: Annotated[List[float], VectorStoreRecordVectorField(
        dimensions=1536,
        distance_function=DistanceFunction.COSINE_DISTANCE,
        index_kind=IndexKind.DISK_ANN
    )] = Field(default_factory=list)
