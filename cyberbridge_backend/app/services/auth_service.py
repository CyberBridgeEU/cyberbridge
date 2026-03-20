# auth_controller.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..repositories import user_repository
from app.services.security_service import verify_password

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


# Token model
class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None
    must_change_password: Optional[bool] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# OAuth2 scheme for token extraction from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def authenticate_user(db: Session, email: str, password: str):
    user = user_repository.get_user_by_email(db, email=email)
    if not user:
        return {"status": "user_not_found"}
    if user.auth_provider != "local":
        return {"status": "sso_user", "auth_provider": user.auth_provider}
    if not verify_password(password, user.hashed_password):
        return {"status": "invalid_password"}
    # Check if user status is active
    if user.status != "active":
        return {"status": "user_not_approved", "user_status": user.status}
    return {"status": "success", "user": user}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try JWT first
    jwt_failed = False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            jwt_failed = True
        else:
            token_data = TokenData(email=email)
            user = user_repository.get_user_by_email(db, email=token_data.email)
            if user is None:
                jwt_failed = True
            else:
                request.state.user = user
                return user
    except JWTError:
        jwt_failed = True

    # Fallback: check X-API-Key header
    if jwt_failed:
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            from app.services.api_key_service import validate_api_key
            user = validate_api_key(db, api_key_header)
            if user is not None:
                request.state.user = user
                return user

    raise credentials_exception


def get_current_active_user(current_user=Depends(get_current_user)):
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Role-based access control
def check_user_role(allowed_roles: list):
    def check_role(current_user=Depends(get_current_user)):
        if current_user.role_name not in allowed_roles or current_user.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Insufficient permissions")
        return current_user
    return check_role
