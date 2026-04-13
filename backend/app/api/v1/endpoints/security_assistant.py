"""
Security AI Assistant Endpoints - Natural Language Security Queries
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt
from pymongo.database import Database

from app.core.config import settings
from app.core.database import get_db
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


def _get_current_user_id(token: Optional[str], db: Database) -> Optional[str]:
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


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    db: Database = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Chat with AI Security Assistant
    Natural language interface for security queries
    """
    current_user_id = _get_current_user_id(token, db)
    response, suggestions = build_security_response(request.message, db)
    
    conversation_id = request.conversation_id or f"conv_{int(datetime.utcnow().timestamp())}"

    db["assistant_messages"].insert_many(
        [
            {
                "conversation_id": conversation_id,
                "user_id": current_user_id,
                "role": "user",
                "content": request.message,
                "created_at": datetime.utcnow(),
            },
            {
                "conversation_id": conversation_id,
                "user_id": current_user_id,
                "role": "assistant",
                "content": response,
                "created_at": datetime.utcnow(),
            },
        ]
    )
    log_audit_event(
        db,
        action="assistant.chat",
        user_id=current_user_id,
        resource_type="assistant_thread",
        resource_id=conversation_id,
        details={"message_length": len(request.message)},
    )
    
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
    db: Database = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Get conversation history
    """
    current_user_id = _get_current_user_id(token, db)

    filters = {"conversation_id": conversation_id}
    if current_user_id is not None:
        filters["user_id"] = current_user_id

    messages = list(db["assistant_messages"].find(filters).sort("created_at", 1))

    return ConversationResponse(
        conversation_id=conversation_id,
        messages=[
            ConversationMessage(
                role=message.get("role", "assistant"),
                content=message.get("content", ""),
                timestamp=message.get("created_at").isoformat()
                if hasattr(message.get("created_at"), "isoformat")
                else str(message.get("created_at")),
            )
            for message in messages
        ],
    )


@router.post("/feedback")
async def submit_feedback(
    conversation_id: str,
    rating: int,
    feedback: Optional[str] = None,
    db: Database = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Submit feedback for AI responses
    """
    current_user_id = _get_current_user_id(token, db)
    db["assistant_feedback"].insert_one(
        {
            "conversation_id": conversation_id,
            "user_id": current_user_id,
            "rating": rating,
            "feedback": feedback,
            "created_at": datetime.utcnow(),
        }
    )
    log_audit_event(
        db,
        action="assistant.feedback",
        user_id=current_user_id,
        resource_type="assistant_thread",
        resource_id=conversation_id,
        details={"rating": rating},
    )

    return {
        "message": "Feedback received",
        "conversation_id": conversation_id,
        "rating": rating
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Database = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Delete a stored conversation thread and its feedback.
    """
    current_user_id = _get_current_user_id(token, db)

    msg_filters = {"conversation_id": conversation_id}
    fb_filters = {"conversation_id": conversation_id}
    if current_user_id is not None:
        msg_filters["user_id"] = current_user_id
        fb_filters["user_id"] = current_user_id

    deleted_messages = db["assistant_messages"].delete_many(msg_filters).deleted_count
    deleted_feedback = db["assistant_feedback"].delete_many(fb_filters).deleted_count
    log_audit_event(
        db,
        action="assistant.clear_conversation",
        user_id=current_user_id,
        resource_type="assistant_thread",
        resource_id=conversation_id,
        details={"deleted_messages": deleted_messages, "deleted_feedback": deleted_feedback},
    )

    return {
        "message": "Conversation cleared",
        "conversation_id": conversation_id,
        "deleted_messages": deleted_messages,
        "deleted_feedback": deleted_feedback,
    }
