from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import config

security = HTTPBearer(auto_error=False)

async def verify_master_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not config.master_key:
        return
    
    if not credentials or credentials.credentials != config.master_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")