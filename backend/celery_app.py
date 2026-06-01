"""Celery application factory for SentinelAI.

This module exposes a `celery` instance which can be used by the worker
process. Broker and result backend are taken from `REDIS_URL` env var.
"""
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery(
    "sentinelai",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Default queue routing (simple default)
celery.conf.task_routes = {"app.tasks.*": {"queue": "default"}}
