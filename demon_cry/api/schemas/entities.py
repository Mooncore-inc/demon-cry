from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

RELATION_PATTERN = r"^[a-z0-9_-]{1,64}$"


class EntityCreate(BaseModel):
    type: str | None = Field(default=None, max_length=64)
    value: str = Field(min_length=1, max_length=1024)
    label: str | None = Field(default=None, max_length=256)
    data: dict = Field(default_factory=dict)


class EntityUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=256)
    data: dict | None = None


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    investigate_id: int
    type: str | None
    value: str
    label: str | None
    data: dict
    source: str
    source_run_id: int | None
    created_at: datetime


class EntityDetailResponse(EntityResponse):
    incoming: list["EntityLinkResponse"]
    outgoing: list["EntityLinkResponse"]


class EntityLinkCreate(BaseModel):
    target_id: int
    relation: str = Field(default="related_to", pattern=RELATION_PATTERN)
    data: dict | None = None


class EntityLinkUpdate(BaseModel):
    relation: str | None = Field(default=None, pattern=RELATION_PATTERN)
    data: dict | None = None


class EntityLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    investigate_id: int
    source_id: int
    target_id: int
    relation: str
    origin: str
    source_run_id: int | None
    data: dict | None
    created_at: datetime


class EntityGraphResponse(BaseModel):
    nodes: list[EntityResponse]
    edges: list[EntityLinkResponse]
