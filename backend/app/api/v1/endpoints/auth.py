"""
Authentication Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import User
from app.services.audit import log_audit_event
from app.schemas import TokenResponse, UserCreate, UserLogin, UserOut

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        log_audit_event(
            db,
            action="auth.login.failed",
            resource_type="auth",
            status="failed",
            severity="warning",
            details={"email": credentials.email},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(subject=str(user.id))
    log_audit_event(
        db,
        action="auth.login.success",
        user_id=user.id,
        resource_type="auth",
        resource_id=str(user.id),
        details={"email": user.email},
    )
    db.commit()
    return TokenResponse(access_token=token, user=user)


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        log_audit_event(
            db,
            action="auth.register.failed",
            resource_type="auth",
            status="failed",
            severity="warning",
            details={"email": user_data.email, "reason": "already_exists"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        organization=user_data.organization,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    log_audit_event(
        db,
        action="auth.register.success",
        user_id=user.id,
        resource_type="auth",
        resource_id=str(user.id),
        details={"email": user.email},
    )
    db.commit()
    return TokenResponse(access_token=token, user=user)


@router.post("/logout")
def logout():
    """
    User logout endpoint
    """
    # Client-side token removal is handled in the frontend.
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user
