from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvestigateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)


class InvestigateExecuteRequest(BaseModel):
    """Тело execute: `{"params": {...}, "context_entity_ids": [..]}`.

    Backward compat: плоский dict без ключа `params` трактуется как целиком
    `params` (`context_entity_ids=[]`).
    """

    params: dict = Field(default_factory=dict)
    context_entity_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _legacy_flat_body(cls, data: object) -> object:
        if isinstance(data, dict) and "params" not in data:
            return {"params": data}
        return data


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
