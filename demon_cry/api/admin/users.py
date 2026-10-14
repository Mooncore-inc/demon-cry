import secrets

from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import UoWDep
from demon_cry.api.schemas.users import UserCreate, UserResponse, UserUpdate
from demon_cry.utils.security import hash_token

users_router = APIRouter(prefix="/users")


@users_router.post(path="/", status_code=201, response_model=UserResponse)
async def create_user(body: UserCreate, uow: UoWDep):
    token = secrets.token_urlsafe(32)
    async with uow.transaction():
        user = await uow.users.create(
            username=body.username, credentials=hash_token(token)
        )
    return UserResponse(
        id=user.id,
        username=user.username,
        credentials=token,
        is_admin=user.is_admin,
    )


@users_router.get(path="/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, uow: UoWDep):
    user = await uow.users.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@users_router.patch(path="/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, body: UserUpdate, uow: UoWDep):
    user = await uow.users.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    async with uow.transaction():
        return await uow.users.update(user, **body.model_dump(exclude_unset=True))


@users_router.delete(path="/{user_id}", status_code=204)
async def delete_user(user_id: int, uow: UoWDep):
    user = await uow.users.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    async with uow.transaction():
        await uow.users.delete(user)
