import secrets
from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import UserRepo
from demon_cry.api.schemas.users import UserResponse, UserCreate, UserUpdate

users_router = APIRouter(prefix="/users")

@users_router.post(path="/", status_code=201, response_model=UserResponse)
async def create_user(body: UserCreate, user_repo: UserRepo):
    token = secrets.token_urlsafe(32)

    user = await user_repo.create(
        username=body.username,
        credentials=token
    )
    return user

@users_router.get(path="/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, user_repo: UserRepo):
    user = await user_repo.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@users_router.patch(path="/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, body: UserUpdate, user_repo: UserRepo):
    user = await user_repo.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await user_repo.update(user, **body.model_dump(exclude_unset=True))

@users_router.delete(path="/{user_id}", status_code=204)
async def delete_user(user_id: int, user_repo: UserRepo):
    user = await user_repo.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_repo.delete(user)
