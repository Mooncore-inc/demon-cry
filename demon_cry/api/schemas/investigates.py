from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InvestigateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)


class InvestigateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    created_at: datetime


class InvestigateUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=256)


class InvestigateDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    investigate_id: int
    plugin_name: str
    status: str
    entities: dict
    errors: dict
    created_at: datetime
