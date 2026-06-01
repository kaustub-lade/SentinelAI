"""
Authentication Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from bson import ObjectId
from pymongo.database import Database

from app.core.config import settings
from app.core.limiter import limiter
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    verify_password,
)
from app.services.audit import log_audit_event
from app.schemas import TokenResponse, UserCreate, UserLogin, UserOut

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _serialize_user(user_doc: dict) -> dict:
    return {
        "id": str(user_doc["_id"]),
        "email": user_doc["email"],
        "full_name": user_doc.get("full_name", ""),
        "organization": user_doc.get("organization"),
        "role": user_doc.get("role", "user"),
        "is_active": user_doc.get("is_active", True),
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(credentials: UserLogin, request: Request, db: Database = Depends(get_db)):
    user = db["users"].find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        log_audit_event(
            db,
            action="auth.login.failed",
            resource_type="auth",
            status="failed",
            severity="warning",
            details={"email": credentials.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(subject=str(user["_id"]))
    refresh_token = create_refresh_token(subject=str(user["_id\"]))
    # store refresh token hash in DB for revocation (store token itself hashed)
    db["users"].update_one({"_id": user["_id"]}, {"$set": {"refresh_token": refresh_token}})
    log_audit_event(
        db,
        action="auth.login.success",
        user_id=str(user["_id"]),
        resource_type="auth",
        resource_id=str(user["_id"]),
        details={"email": user["email"]},
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=_serialize_user(user))


@router.post("/register")
def register(user_data: UserCreate, db: Database = Depends(get_db)):
    existing_user = db["users"].find_one({"email": user_data.email})
    if existing_user:
        log_audit_event(
            db,
            action="auth.register.failed",
            resource_type="auth",
            status="failed",
            severity="warning",
            details={"email": user_data.email, "reason": "already_exists"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    insert_result = db["users"].insert_one(
        {
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "full_name": user_data.full_name,
            "organization": user_data.organization,
            "role": "user",
            "is_active": True,
        }
    )
    user = db["users"].find_one({"_id": insert_result.inserted_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    access_token = create_access_token(subject=str(user["_id"]))
    refresh_token = create_refresh_token(subject=str(user["_id"]))
    db["users"].update_one({"_id": user["_id"]}, {"$set": {"refresh_token": refresh_token}})
    log_audit_event(
        db,
        action="auth.register.success",
        user_id=str(user["_id"]),
        resource_type="auth",
        resource_id=str(user["_id"]),
        details={"email": user["email"]},
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=_serialize_user(user))


@router.post("/logout")
def logout():
    """
    User logout endpoint
    """
    # For revocation, the frontend should call /token/revoke and include
    # authentication. Here we leave logout as a simple client-side op.
    return {"message": "Logged out successfully"}



@router.post("/token/refresh", response_model=TokenResponse)
def refresh_token(request: dict, db: Database = Depends(get_db)):
    """Exchange a refresh token for a new access token. Expects JSON {"refresh_token": "..."}

    This endpoint will validate the JWT refresh token and ensure it matches
    the latest stored refresh token for the user (simple rotation strategy).
    """
    token = request.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token")

    user_id = verify_refresh_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        user = db["users"].find_one({"_id": ObjectId(str(user_id))})
    except Exception:
        user = None

    if user is None or user.get("refresh_token") != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or invalid")

    new_access = create_access_token(subject=str(user["_id"]))
    # rotate refresh token
    new_refresh = create_refresh_token(subject=str(user["_id"]))
    db["users"].update_one({"_id": user["_id"]}, {"$set": {"refresh_token": new_refresh}})

    return TokenResponse(access_token=new_access, refresh_token=new_refresh, user=_serialize_user(user))


@router.post("/token/revoke")
def revoke_token(request: dict, db: Database = Depends(get_db)):
    """Revoke a refresh token (client provides the token to revoke)."""
    token = request.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token")

    user_id = verify_refresh_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        user = db["users"].find_one({"_id": ObjectId(str(user_id))})
    except Exception:
        user = None

    if user and user.get("refresh_token") == token:
        db["users"].update_one({"_id": user["_id"]}, {"$unset": {"refresh_token": ""}})
    return {"message": "Refresh token revoked"}


@router.get("/me", response_model=UserOut)
def me(token: str = Depends(oauth2_scheme), db: Database = Depends(get_db)):
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

    return _serialize_user(user)
