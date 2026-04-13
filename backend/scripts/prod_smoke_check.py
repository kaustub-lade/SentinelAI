#!/usr/bin/env python3
"""Production smoke checks for SentinelAI backend.

Usage:
  python backend/scripts/prod_smoke_check.py --backend-url https://sentinelai-3glx.onrender.com
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from typing import Any

import requests


def _url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


def _assert_status(response: requests.Response, expected: int, name: str) -> None:
    if response.status_code != expected:
        raise RuntimeError(
            f"{name} failed: expected HTTP {expected}, got {response.status_code}, body={response.text[:500]}"
        )


def run_smoke_checks(backend_url: str, timeout_seconds: int) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    summary: dict[str, Any] = {"backend_url": backend_url, "checks": []}

    # 1) Health check
    health = session.get(_url(backend_url, "/health"), timeout=timeout_seconds)
    _assert_status(health, 200, "health")
    health_body = health.json()
    summary["checks"].append({"name": "health", "status": "ok", "body": health_body})

    # 2) Register a unique smoke user
    email = f"prod_smoke_{uuid.uuid4().hex[:12]}@example.com"
    password = f"ProdSmoke#{uuid.uuid4().hex[:8]}"
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Prod Smoke",
        "organization": "SentinelAI",
    }
    register_resp = session.post(
        _url(backend_url, "/api/v1/auth/register"),
        json=register_payload,
        timeout=timeout_seconds,
    )
    _assert_status(register_resp, 200, "auth.register")
    summary["checks"].append({"name": "auth.register", "status": "ok"})

    # 3) Login
    login_resp = session.post(
        _url(backend_url, "/api/v1/auth/login"),
        json={"email": email, "password": password},
        timeout=timeout_seconds,
    )
    _assert_status(login_resp, 200, "auth.login")
    token = login_resp.json().get("access_token")
    if not token:
        raise RuntimeError("auth.login failed: missing access_token")
    summary["checks"].append({"name": "auth.login", "status": "ok"})

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 4) /auth/me
    me_resp = session.get(_url(backend_url, "/api/v1/auth/me"), headers=auth_headers, timeout=timeout_seconds)
    _assert_status(me_resp, 200, "auth.me")
    summary["checks"].append({"name": "auth.me", "status": "ok"})

    # 5) Vulnerability stats
    vuln_resp = session.get(_url(backend_url, "/api/v1/vulnerabilities/stats"), timeout=timeout_seconds)
    _assert_status(vuln_resp, 200, "vulnerabilities.stats")
    summary["checks"].append({"name": "vulnerabilities.stats", "status": "ok"})

    # 6) Phishing URL check
    phishing_resp = session.post(
        _url(backend_url, "/api/v1/phishing/check-url"),
        params={"url": "https://example.com/login"},
        timeout=timeout_seconds,
    )
    _assert_status(phishing_resp, 200, "phishing.check-url")
    summary["checks"].append({"name": "phishing.check-url", "status": "ok"})

    # 7) Assistant chat
    conversation_id = f"prod_smoke_{int(time.time())}"
    chat_resp = session.post(
        _url(backend_url, "/api/v1/assistant/chat"),
        json={"message": "show me security summary", "conversation_id": conversation_id},
        headers=auth_headers,
        timeout=timeout_seconds,
    )
    _assert_status(chat_resp, 200, "assistant.chat")
    summary["checks"].append({"name": "assistant.chat", "status": "ok"})

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run production smoke checks against SentinelAI backend")
    parser.add_argument("--backend-url", required=True, help="Backend base URL, e.g. https://sentinelai-3glx.onrender.com")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout per request in seconds")
    args = parser.parse_args()

    try:
        result = run_smoke_checks(args.backend_url, args.timeout)
        print("SMOKE CHECK PASSED")
        for item in result["checks"]:
            print(f"- {item['name']}: {item['status']}")
        return 0
    except Exception as exc:
        print(f"SMOKE CHECK FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
