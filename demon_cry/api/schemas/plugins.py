from pydantic import BaseModel


class PluginResponse(BaseModel):
    id: int
    plugin_name: str
    config: dict
    enabled: bool


class PluginUpdate(BaseModel):
    config: dict | None = None
    enabled: bool | None = None
