from __future__ import annotations

from typing import Optional

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pymongo.database import Database

from app.core.config import settings
from app.core.database import get_db

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _serialize_user(user_doc: dict) -> dict:
    return {
        "id": str(user_doc["_id"]),
        "email": user_doc["email"],
        "full_name": user_doc.get("full_name", ""),
        "organization": user_doc.get("organization"),
        "role": user_doc.get("role", "user"),
        "is_active": user_doc.get("is_active", True),
    }


def get_current_user_id(token: Optional[str], db: Database) -> Optional[str]:
    if not token:
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    try:
        user = db["users"].find_one({"_id": ObjectId(str(user_id))})
    except Exception:
        user = None

    if user is None:
        raise credentials_exception

    return str(user["_id"])


def get_current_user(token: Optional[str], db: Database) -> dict:
    user_id = get_current_user_id(token, db)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = db["users"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _serialize_user(user)


def require_roles(*allowed_roles: str):
    def dependency(token: Optional[str] = Depends(oauth2_scheme_optional), db: Database = Depends(get_db)):
        user = get_current_user(token, db)
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
