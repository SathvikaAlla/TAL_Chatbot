from typing import Dict, List, Optional, Annotated
from pydantic import BaseModel, BeforeValidator, Field, field_validator  # Use Pydantic's Field
from semantic_kernel.data import (
    DistanceFunction,
    IndexKind,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)

class LampConnections(BaseModel):
    min: int
    max: int
    @field_validator('min', 'max', mode='before')
    def convert_strings(cls, v):
        return int(v) if isinstance(v, str) else v
    
@vectorstoremodel
class PowerConverterVector(BaseModel):
    id: Annotated[str, VectorStoreRecordKeyField]
    artnr: Annotated[int, VectorStoreRecordDataField()] = Field(..., alias="ARTNR")
    ip_rating: Annotated[int, VectorStoreRecordDataField()] = Field(..., alias="IP")
    type: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="TYPE")
    lamps: Optional[Dict[str, LampConnections]] = None

    name: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="Name")
    efficiency: Optional[Annotated[float, VectorStoreRecordDataField()]] = Field(None, alias="EFFICIENCY @full load")
    pdf_link: Optional[Annotated[str, VectorStoreRecordDataField()]] = None
    converter_description: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="CONVERTER DESCRIPTION:")
    nom_input_voltage: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="NOM. INPUT VOLTAGE (V)")
    output_voltage: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="OUTPUT VOLTAGE (V)")
    unit: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="Unit")
    price: Optional[Annotated[float, VectorStoreRecordDataField()]] = Field(None, alias="Listprice")
    life_cycle: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="LifeCycle")
    size: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="SIZE: L*B*H (mm)")
    ccr_amplitude: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="CCR (AMPLITUDE)")
    dimmability: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="DIMMABILITY")
    dim_list_type: Optional[Annotated[str, VectorStoreRecordDataField()]] = Field(None, alias="DIMLIST TYPE")
    similarity_score: Optional[Annotated[float, VectorStoreRecordDataField()]] = Field(None, alias="SimilarityScore")
    embedding: Annotated[List[float], VectorStoreRecordVectorField(
        dimensions=1536,
        distance_function=DistanceFunction.COSINE_DISTANCE,
        index_kind=IndexKind.DISK_ANN
    )] = Field(default_factory=list)
