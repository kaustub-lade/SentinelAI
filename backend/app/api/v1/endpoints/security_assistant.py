"""
Security AI Assistant Endpoints - Natural Language Security Queries
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.models import AssistantFeedback, AssistantMessage, User
from app.services.audit import log_audit_event
from app.services.assistant_context import build_security_response

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    suggestions: Optional[List[str]] = None


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: List[ConversationMessage]


def _get_current_user_id(token: Optional[str], db: Session) -> Optional[int]:
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

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user.id


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Chat with AI Security Assistant
    Natural language interface for security queries
    """
    current_user_id = _get_current_user_id(token, db)
    response, suggestions = build_security_response(request.message, db)
    
    conversation_id = request.conversation_id or f"conv_{int(datetime.utcnow().timestamp())}"

    user_message = AssistantMessage(
        conversation_id=conversation_id,
        user_id=current_user_id,
        role="user",
        content=request.message,
    )
    assistant_message = AssistantMessage(
        conversation_id=conversation_id,
        user_id=current_user_id,
        role="assistant",
        content=response,
    )
    db.add(user_message)
    db.add(assistant_message)
    log_audit_event(
        db,
        action="assistant.chat",
        user_id=current_user_id,
        resource_type="assistant_thread",
        resource_id=conversation_id,
        details={"message_length": len(request.message)},
    )
    db.commit()
    
    return ChatResponse(
        response=response,
        conversation_id=conversation_id,
        suggestions=suggestions
    )


@router.get("/suggestions")
async def get_quick_suggestions():
    """
    Get quick action suggestions
    """
    return {
        "suggestions": [
            "What are my critical vulnerabilities?",
            "Show me today's threat summary",
            "Is my system secure?",
            "What malware was detected recently?",
            "Check for phishing attempts",
            "Explain CVE-2024-3094",
            "How can I improve security?",
            "What's my current risk score?"
        ]
    }


@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Get conversation history
    """
    current_user_id = _get_current_user_id(token, db)

    query = db.query(AssistantMessage).filter(AssistantMessage.conversation_id == conversation_id)
    if current_user_id is not None:
        query = query.filter(AssistantMessage.user_id == current_user_id)

    messages = query.order_by(AssistantMessage.created_at.asc(), AssistantMessage.id.asc()).all()

    return ConversationResponse(
        conversation_id=conversation_id,
        messages=[
            ConversationMessage(
                role=message.role,
                content=message.content,
                timestamp=message.created_at.isoformat(),
            )
            for message in messages
        ],
    )


@router.post("/feedback")
async def submit_feedback(
    conversation_id: str,
    rating: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Submit feedback for AI responses
    """
    current_user_id = _get_current_user_id(token, db)
    db_feedback = AssistantFeedback(
        conversation_id=conversation_id,
        user_id=current_user_id,
        rating=rating,
        feedback=feedback,
    )
    db.add(db_feedback)
    log_audit_event(
        db,
        action="assistant.feedback",
        user_id=current_user_id,
        resource_type="assistant_thread",
        resource_id=conversation_id,
        details={"rating": rating},
    )
    db.commit()

    return {
        "message": "Feedback received",
        "conversation_id": conversation_id,
        "rating": rating
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Delete a stored conversation thread and its feedback.
    """
    current_user_id = _get_current_user_id(token, db)

    message_query = db.query(AssistantMessage).filter(AssistantMessage.conversation_id == conversation_id)
    feedback_query = db.query(AssistantFeedback).filter(AssistantFeedback.conversation_id == conversation_id)

    if current_user_id is not None:
        message_query = message_query.filter(AssistantMessage.user_id == current_user_id)
        feedback_query = feedback_query.filter(AssistantFeedback.user_id == current_user_id)

    deleted_messages = message_query.delete(synchronize_session=False)
    deleted_feedback = feedback_query.delete(synchronize_session=False)
    log_audit_event(
        db,
        action="assistant.clear_conversation",
        user_id=current_user_id,
        resource_type="assistant_thread",
        resource_id=conversation_id,
        details={"deleted_messages": deleted_messages, "deleted_feedback": deleted_feedback},
    )
    db.commit()

    return {
        "message": "Conversation cleared",
        "conversation_id": conversation_id,
        "deleted_messages": deleted_messages,
        "deleted_feedback": deleted_feedback,
    }
