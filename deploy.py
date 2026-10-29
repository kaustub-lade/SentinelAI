"""SentinelAI deploy helper (Render + Vercel).

Reads credentials from <repo>/.deploy-secrets, which must contain at minimum:

    RENDER_API_KEY=...
    VERCEL_TOKEN=...
    MONGODB_URL=mongodb+srv://...
    GROQ_API_KEY=...
    VIRUSTOTAL_API_KEY=...
    NVD_API_KEY=...
    SECRET_KEY=...            (optional, generated if absent)

Usage:
    python deploy.py status     # read-only inspection
    python deploy.py apply      # set env vars + redeploy + poll health
    python deploy.py vercel     # point Vercel at the live backend and redeploy
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent
SECRETS_FILE = REPO / ".deploy-secrets"
BACKEND_ENV = REPO / "backend" / ".env"
FRONTEND_ORIGIN = "https://sentinel-ai-flame.vercel.app"
SERVICE_HINT = "sentinelai"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def load_secrets() -> dict[str, str]:
    """Tokens from .deploy-secrets, everything else borrowed from backend/.env."""
    if not SECRETS_FILE.exists():
        raise SystemExit(
            f"missing secrets file: {SECRETS_FILE}\n"
            "It only needs:\n  RENDER_API_KEY=rnd_...\n  VERCEL_TOKEN=..."
        )
    out = _parse_env_file(BACKEND_ENV)
    out.update(_parse_env_file(SECRETS_FILE))
    for required in ("RENDER_API_KEY", "VERCEL_TOKEN"):
        if not out.get(required):
            raise SystemExit(f"{required} is missing from {SECRETS_FILE}")
    return out


def http(method: str, url: str, token: str, body=None, header: str = "Authorization"):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header(header, f"Bearer {token}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = resp.read().decode()
            return resp.status, (json.loads(payload) if payload.strip() else None)
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = payload
        return exc.code, parsed


def render(method: str, path: str, secrets: dict[str, str], body=None):
    return http(method, f"https://api.render.com/v1{path}", secrets["RENDER_API_KEY"], body)


def vercel(method: str, path: str, secrets: dict[str, str], body=None):
    return http(method, f"https://api.vercel.com{path}", secrets["VERCEL_TOKEN"], body)


def find_service(secrets: dict[str, str]):
    status, data = render("GET", "/services?limit=100", secrets)
    if status != 200:
        raise SystemExit(f"Render services lookup failed ({status}): {data}")
    services = [item.get("service", item) for item in data]
    matches = [
        s
        for s in services
        if SERVICE_HINT in (s.get("name") or "").lower()
        or SERVICE_HINT in (s.get("serviceDetails", {}).get("url") or "").lower()
    ]
    return matches


def describe_service(service: dict) -> str:
    details = service.get("serviceDetails") or {}
    repo = details.get("repo") or "?"
    branch = details.get("branch") or "?"
    url = details.get("url") or "?"
    suspended = service.get("suspended")
    return (
        f"id={service.get('id')}\n"
        f"  name={service.get('name')}\n"
        f"  type={service.get('type')} runtime={service.get('runtime', details.get('runtime'))}\n"
        f"  url=https://{url}\n"
        f"  repo={repo} branch={branch}\n"
        f"  autoDeploy={service.get('autoDeploy')} suspended={suspended}"
    )


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def cmd_status(secrets: dict[str, str]) -> None:
    print("== Render ==")
    services = find_service(secrets)
    if not services:
        print("no Render service matching 'sentinelai' found on this account")
        status, _ = render("GET", "/services?limit=1", secrets)
        print(f"(services endpoint reachable, status {status})")
    for service in services:
        print(describe_service(service))
        status, env_vars = render("GET", f"/services/{service['id']}/env-vars?limit=100", secrets)
        if status == 200:
            keys = sorted(item["envVar"]["key"] for item in env_vars)
            print("  env keys:", ", ".join(keys))

    print("\n== Vercel ==")
    status, data = vercel("GET", "/v9/projects?limit=100", secrets)
    if status != 200:
        print(f"Vercel projects lookup failed ({status}): {data}")
        return
    for project in data.get("projects", []):
        if SERVICE_HINT in project.get("name", "").lower():
            print(
                f"id={project.get('id')} name={project.get('name')} "
                f"framework={project.get('framework')} domains={project.get('alias')}"
            )
            st, envs = vercel("GET", f"/v9/projects/{project['id']}/env?decrypt=true", secrets)
            if st == 200:
                for env in envs.get("envs", []):
                    print(f"  env {env['key']} ({','.join(env.get('target') or [])}) = {env.get('value')!r}")


def desired_env(secrets: dict[str, str]) -> list[dict[str, str]]:
    secret_key = secrets.get("SECRET_KEY")
    if not secret_key:
        secret_key = secrets.setdefault("SECRET_KEY", __import__("secrets").token_urlsafe(48))
    return [
        {"key": "MONGODB_URL", "value": secrets["MONGODB_URL"]},
        {"key": "MONGODB_DB_NAME", "value": "sentinelai"},
        {"key": "SECRET_KEY", "value": secret_key},
        {"key": "ALGORITHM", "value": "HS256"},
        {"key": "ACCESS_TOKEN_EXPIRE_MINUTES", "value": "30"},
        {"key": "ENVIRONMENT", "value": "production"},
        {"key": "ALLOWED_ORIGINS", "value": FRONTEND_ORIGIN},
        {"key": "GROQ_API_KEY", "value": secrets["GROQ_API_KEY"]},
        {"key": "GROQ_MODEL", "value": "openai/gpt-oss-120b"},
        {"key": "VIRUSTOTAL_API_KEY", "value": secrets["VIRUSTOTAL_API_KEY"]},
        {"key": "NVD_API_KEY", "value": secrets["NVD_API_KEY"]},
    ]


def cmd_apply(secrets: dict[str, str]) -> None:
    services = find_service(secrets)
    if not services:
        raise SystemExit(
            "No Render service found. The service must exist (or be created from a Git repo) "
            "before I can configure it."
        )
    service = services[0]
    sid = service["id"]
    print(describe_service(service))

    status, existing = render("GET", f"/services/{sid}/env-vars?limit=100", secrets)
    current = {item["envVar"]["key"]: item["envVar"]["value"] for item in existing} if status == 200 else {}
    payload = []
    for item in desired_env(secrets):
        value = item["value"] or current.get(item["key"], "")
        if not value:
            raise SystemExit(f"refusing to set empty env var {item['key']} (add it to .deploy-secrets)")
        payload.append({"key": item["key"], "value": value})
    # keep any unrelated vars the service already had
    for key, value in current.items():
        if key not in {p["key"] for p in payload}:
            payload.append({"key": key, "value": value})

    status, data = render("PUT", f"/services/{sid}/env-vars", secrets, payload)
    print(f"env vars update -> {status}")
    if status >= 300:
        print(data)
        raise SystemExit(1)

    status, deploy = render("POST", f"/services/{sid}/deploys", secrets, {"clearCache": "do_not_clear"})
    print(f"trigger deploy -> {status}")
    if status >= 300:
        print(deploy)
        raise SystemExit(1)
    deploy_id = deploy.get("id")
    print(f"deploy id: {deploy_id}")

    deadline = time.time() + 20 * 60
    last = None
    while time.time() < deadline:
        time.sleep(20)
        st, info = render("GET", f"/services/{sid}/deploys/{deploy_id}", secrets)
        if st != 200:
            print(f"poll -> {st} {info}")
            continue
        state = info.get("status")
        if state != last:
            print(f"[{time.strftime('%H:%M:%S')}] deploy status: {state}")
            last = state
        if state == "live":
            print("deploy is live")
            break
        if state in {"build_failed", "update_failed", "canceled", "pre_deploy_failed"}:
            raise SystemExit(f"deploy failed: {json.dumps(info)[:2000]}")
    else:
        print("timed out waiting for deploy; check the Render dashboard")

    url = f"https://{(service.get('serviceDetails') or {}).get('url')}"
    print(f"health: {url}/health")
    print(health(url))


def health(base: str) -> str:
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=120) as resp:
            return f"{resp.status} {resp.read().decode()[:200]}"
    except Exception as exc:  # noqa: BLE001
        return f"FAILED {type(exc).__name__}: {exc}"


def cmd_vercel(secrets: dict[str, str]) -> None:
    backend = secrets.get("BACKEND_URL", "").rstrip("/")
    if not backend:
        raise SystemExit("set BACKEND_URL=https://... in .deploy-secrets first")

    status, data = vercel("GET", "/v9/projects?limit=100", secrets)
    if status != 200:
        raise SystemExit(f"Vercel projects lookup failed ({status}): {data}")
    projects = [p for p in data.get("projects", []) if SERVICE_HINT in p.get("name", "").lower()]
    if not projects:
        raise SystemExit("no Vercel project matching 'sentinelai'")
    project = projects[0]
    pid = project["id"]
    print(f"project: {project['name']} ({pid})")

    payload = {
        "key": "VITE_API_URL",
        "value": backend,
        "type": "plain",
        "target": ["production", "preview", "development"],
    }
    st, envs = vercel("GET", f"/v9/projects/{pid}/env?decrypt=true", secrets)
    existing = [e for e in (envs.get("envs") or []) if e.get("key") == "VITE_API_URL"] if st == 200 else []
    if existing:
        for env in existing:
            code, body = vercel("PATCH", f"/v9/projects/{pid}/env/{env['id']}", secrets, {"value": backend})
            print(f"update VITE_API_URL ({env['id']}) -> {code} {body if code >= 300 else ''}")
    else:
        code, body = vercel("POST", f"/v10/projects/{pid}/env", secrets, payload)
        print(f"create VITE_API_URL -> {code} {body if code >= 300 else ''}")

    # also patch the committed fallback so a stale bundle can never point at a dead host
    print("\nnext: rebuild the frontend (npm run build in frontend/, then deploy)")

    code, dep = vercel("POST", "/v13/deployments", secrets, {
        "name": project["name"],
        "project": pid,
        "target": "production",
    })
    print(f"trigger deployment -> {code}")
    if code >= 300:
        print(dep)
        return
    print("deployment:", dep.get("id"), dep.get("url"))


def main() -> None:
    secrets = load_secrets()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        cmd_status(secrets)
    elif cmd == "apply":
        cmd_apply(secrets)
    elif cmd == "vercel":
        cmd_vercel(secrets)
    else:
        raise SystemExit(f"unknown command {cmd!r}; use status|apply|vercel")


if __name__ == "__main__":
    main()
