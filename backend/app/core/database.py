import logging

from fastapi import HTTPException, status
from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings


logger = logging.getLogger(__name__)

mongo_client = (
    MongoClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
    )
    if settings.MONGODB_URL
    else None
)
mongo_db = mongo_client[settings.MONGODB_DB_NAME] if mongo_client else None


def is_db_available() -> bool:
    if mongo_client is None:
        logger.error("MongoDB connectivity check failed: MONGODB_URL is not configured")
        return False

    try:
        mongo_client.admin.command("ping")
        return True
    except PyMongoError as exc:
        logger.error("MongoDB connectivity check failed: %s", exc)
        return False


def ensure_indexes() -> bool:
    if mongo_db is None:
        logger.error("MongoDB index initialization failed: MONGODB_URL is not configured")
        return False

    try:
        mongo_db["users"].create_index([("email", ASCENDING)], unique=True)
        mongo_db["cve_records"].create_index([("cve_id", ASCENDING)], unique=True)
        mongo_db["assistant_messages"].create_index([("conversation_id", ASCENDING)])
        mongo_db["assistant_feedback"].create_index([("conversation_id", ASCENDING)])
        mongo_db["audit_logs"].create_index([("created_at", ASCENDING)])
        mongo_db["scans"].create_index([("scan_type", ASCENDING), ("created_at", ASCENDING)])
        return True
    except PyMongoError as exc:
        logger.error("MongoDB index initialization failed: %s", exc)
        return False


def get_db():
    if not is_db_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Check MONGODB_URL/MONGODB_DB_NAME on deployment.",
        )
    yield mongo_db