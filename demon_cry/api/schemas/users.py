from pydantic import BaseModel

class UserResponse(BaseModel):

    id: int
    username: str
    credentials: str
    is_admin: bool

class UserCreate(BaseModel):
    username: str

class UserUpdate(BaseModel):
    username: str | None = None
