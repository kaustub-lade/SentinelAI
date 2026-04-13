"""
Authentication Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from bson import ObjectId
from pymongo.database import Database

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
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
def login(credentials: UserLogin, db: Database = Depends(get_db)):
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

    token = create_access_token(subject=str(user["_id"]))
    log_audit_event(
        db,
        action="auth.login.success",
        user_id=str(user["_id"]),
        resource_type="auth",
        resource_id=str(user["_id"]),
        details={"email": user["email"]},
    )
    return TokenResponse(access_token=token, user=_serialize_user(user))


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

    token = create_access_token(subject=str(user["_id"]))
    log_audit_event(
        db,
        action="auth.register.success",
        user_id=str(user["_id"]),
        resource_type="auth",
        resource_id=str(user["_id"]),
        details={"email": user["email"]},
    )
    return TokenResponse(access_token=token, user=_serialize_user(user))


@router.post("/logout")
def logout():
    """
    User logout endpoint
    """
    # Client-side token removal is handled in the frontend.
    return {"message": "Logged out successfully"}


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
