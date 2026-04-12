from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    scan_type = Column(String(50), nullable=False)
    input_data = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CveRecord(Base):
    __tablename__ = "cve_records"

    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    cvss_score = Column(Float, nullable=False, default=0.0)
    affected_systems = Column(Text, nullable=False, default="")
    exploit_available = Column(Boolean, nullable=False, default=False)
    patch_available = Column(Boolean, nullable=False, default=False)
    risk_score = Column(Integer, nullable=False, default=0)
    published_date = Column(DateTime, nullable=True)
    last_modified = Column(DateTime, nullable=True)


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssistantFeedback(Base):
    __tablename__ = "assistant_feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=True)
    rating = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    action = Column(String(100), index=True, nullable=False)
    resource_type = Column(String(50), index=True, nullable=True)
    resource_id = Column(String(100), index=True, nullable=True)
    status = Column(String(20), nullable=False, default="success")
    severity = Column(String(20), nullable=False, default="info")
    details = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)