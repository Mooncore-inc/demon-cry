from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from demon_cry.database.models.user import UserModel
from demon_cry.utils.dependencies import get_user_repo
from demon_cry.database.repositories.user import UserRepository

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserModel:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing API key")

    user = await user_repo.get(credentials=credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user
