# Manual Tasks Required to Fully Run SentinelAI

This document lists manual steps you must perform locally or in your cloud account to enable features that the assistant scaffolded but cannot complete automatically. Grouped by area, each item includes the purpose, where it is used, and suggested commands or notes.

---

## 1) System / OS Dependencies

- Install libyara (required by `yara-python`) for YARA scanning.
  - Ubuntu/Debian: `sudo apt-get install -y libyara-dev` (or compile from source)
  - Mac (Homebrew): `brew install yara`
  - Windows: install YARA binaries or use WSL for full support.
  - Where used: `backend/app/services/yara_engine.py`, `backend/requirements.txt`.

- Install build tools for `pefile` and other native packages if needed.
  - Ubuntu: `sudo apt-get install -y build-essential python3-dev`

Notes: CI runners may need these system packages installed before `pip install`.

---

## 2) API Keys & External Services (must provide as env vars)

- `VIRUSTOTAL_API_KEY` — VirusTotal v3 API key
  - Used by: `backend/app/services/virus_total.py`, Celery tasks
  - Set in: `.env` or deploy platform (Render/Vercel/GitHub Actions secrets)

- `GROQ_API_KEY` (or OpenAI API key) — LLM assistant
  - Used by: `backend/app/services/assistant_context.py` (may need enabling)
  - Set in `.env` or platform secrets

- `NVD_API_KEY` — optional, for NVD CVE fetches
  - Used by: `backend/app/api/v1/endpoints/vulnerabilities.py`

- `MONGODB_URL` / `MONGODB_DB_NAME` — MongoDB connection string
  - Ensure the database is reachable by backend & worker; set credentials in env

- `SECRET_KEY` — production secret (>=32 chars)
  - Used by JWT signing: `backend/app/core/config.py`

Set these in `.env` (development) or in your cloud provider: e.g., Render environment variables or GitHub Secrets for CI.

Example `.env` (do not commit):

```env
SECRET_KEY=super-secret-32chars-or-more-choose-secure
VIRUSTOTAL_API_KEY=xxx
GROQ_API_KEY=xxx
MONGODB_URL=mongodb://user:pass@host:27017/sentinelai
MONGODB_DB_NAME=sentinelai
REDIS_URL=redis://redis:6379/0
MITRE_DATA_PATH=./backend/app/data/enterprise-attack.json
```

---

## 3) Datasets and Model Training (manual, large downloads)

- EMBER / PE datasets for malware model training
  - Purpose: replace synthetic training with real PE features and labels
  - Where used: `backend/scripts/train_malware_model.py` (example)
  - Action: download EMBER or curated datasets, implement preprocessing, and retrain offline (GPU recommended for large models).

- Phishing datasets (emails/URLs) for NLP training
  - Purpose: improve `phishing_model` beyond the synthetic model.
  - Action: acquire datasets (Phishing corpora, Kaggle, internal), retrain models and store joblib artifacts under `backend/app/ml/`.

Notes: Training can be compute intensive; perform on a workstation or cloud GPU/CPU instance.

---

## 4) YARA Ruleset (curated signatures)

- Obtain a YARA rules repository (e.g., community rules, vendor rules) and place `.yar`/`.yara` files in `yara_rules/` or set `YARA_RULES_DIR` environment variable.
  - Where used: `backend/app/services/yara_engine.py`
  - Suggestion: store rules under `backend/app/yara_rules/` and add to `.dockerignore`/`.gitignore` if proprietary.

---

## 5) Deployment & Infra Setup

- Redis & Celery worker deploy
  - Ensure Redis is available to backend and Celery workers.
  - For Render: add a Redis instance or use external provider; configure `REDIS_URL`.
  - For production, run multiple workers and configure monitoring/retries.

- MongoDB production (Atlas or managed)
  - Provision MongoDB Atlas, configure user, whitelist IPs, and set `MONGODB_URL`.

- Configure a persistent storage location for MITRE JSON if using `mitre_tasks.fetch_mitre_data`.

- TLS/HTTPS and domain
  - Configure reverse proxy or platform-managed TLS.

---

## 6) CI/CD Secrets and System Packages

- Add the API keys and `SECRET_KEY` to GitHub Actions secrets (or use environment secrets in your CI). The CI workflow installs backend requirements; if `yara-python` or system libs cause CI failures, update CI to install required apt packages first.

Example extra CI steps (Ubuntu):

```yaml
- name: Install system deps
  run: sudo apt-get update && sudo apt-get install -y libyara-dev build-essential
```

---

## 7) Email/SMS Provider for MFA & Password Reset

- If you enable MFA or password reset flows, configure an SMTP provider (or SendGrid) and/or SMS gateway. Store credentials in env and update code to use them for verification.

---

## 8) Monitoring & Logging (optional manual steps)

- Configure Prometheus to scrape the `/metrics` endpoint.
- Configure a logging sink (LogDNA, Papertrail, ELK) to collect structured logs emitted by `structlog`.

---

## 9) Frontend Work (you must run/build)

- Ensure `VITE_API_URL` in frontend `.env` points to backend URL.
- Add UI pages for task status and MITRE technique display (I can scaffold, but you'll need to adapt styles and endpoints).

Build commands:

```bash
cd frontend
npm install
npm run build   # or `npm run dev` for development
```

---

## 10) Security Hardening (manual checks)

- Rotate secrets and avoid committing `.env`.
- Run `bandit`, `pip-audit`, and container scanning (Trivy) and remediate findings.
- Use managed identity or secret manager for production secrets instead of plain env files.

---

## 11) Optional: Sandbox / Dynamic Analysis

- To run dynamic malware analysis (Cuckoo/CAPE): provision sandbox hosts (isolated VMs), configure upload and orchestration, integrate with Celery tasks for actual execution.

---

## Quick checklist (minimum to enable core features)

- [ ] Install `libyara` on host/CI
- [ ] Add `VIRUSTOTAL_API_KEY` to `.env` or platform secrets
- [ ] Provision MongoDB and set `MONGODB_URL`
- [ ] Provision Redis and set `REDIS_URL`
- [ ] Add `SECRET_KEY` (>=32 chars)
- [ ] Place YARA rules in `yara_rules/` or set `YARA_RULES_DIR`
- [ ] (Optional) Download MITRE JSON via `app.tasks.fetch_mitre` or run the task manually
- [ ] (Optional) Train models with real datasets and store under `backend/app/ml/`

---

If you want, I can generate shell scripts to automate many of these steps for your environment (WSL/Ubuntu or Mac). Tell me which OS and deployment target you prefer and I'll prepare scripts.
