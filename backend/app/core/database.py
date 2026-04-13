from pymongo import ASCENDING, MongoClient

from app.core.config import settings


mongo_client = MongoClient(settings.MONGODB_URL)
mongo_db = mongo_client[settings.MONGODB_DB_NAME]


def ensure_indexes() -> None:
    mongo_db["users"].create_index([("email", ASCENDING)], unique=True)
    mongo_db["cve_records"].create_index([("cve_id", ASCENDING)], unique=True)
    mongo_db["assistant_messages"].create_index([("conversation_id", ASCENDING)])
    mongo_db["assistant_feedback"].create_index([("conversation_id", ASCENDING)])
    mongo_db["audit_logs"].create_index([("created_at", ASCENDING)])
    mongo_db["scans"].create_index([("scan_type", ASCENDING), ("created_at", ASCENDING)])


def get_db():
    yield mongo_db