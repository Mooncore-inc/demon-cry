from pydantic import BaseModel


class LLMModelResponse(BaseModel):
    id: int
    model_name: str
    base_url: str
    is_default: bool

    model_config = {"from_attributes": True}


class LLMModelCreate(BaseModel):
    model_name: str
    base_url: str
    api_key: str
    is_default: bool = False


class LLMModelUpdate(BaseModel):
    model_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    is_default: bool | None = None
