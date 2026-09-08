from pydantic import BaseModel

class ModuleResponse(BaseModel):

    id: int
    module_name: str
    config: dict
    enabled: bool

class ModuleUpdate(BaseModel):

    config: dict | None
    enabled: bool | None
