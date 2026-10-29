"""Populate the dashboard with real EMBER-2018 benchmark samples.

Reads holdout predictions produced by ``train_ember_model.py`` and writes
scan/alert documents tagged ``source: "ember"``. Everything this script
creates can be removed again with ``--clear``.

Usage:
    python scripts/backfill_ember_dashboard.py                 # write
    python scripts/backfill_ember_dashboard.py --db sentinalai # target the live DB
    python scripts/backfill_ember_dashboard.py --clear         # remove EMBER rows
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

DATASET = "EMBER-2018"
SOURCE = "ember"


def load_holdout(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def severity_for(row: dict) -> tuple[str, str, str]:
    """Return (verdict, threat_level, dashboard_severity)."""
    proba = float(row["probability"])
    if int(row["label"]) == 1:
        if proba >= 0.9:
            return "Malicious", "Critical", "Critical"
        if proba >= 0.6:
            return "Malicious", "High", "High"
        return "Suspicious", "Medium", "Medium"
    if proba >= 0.5:
        return "Suspicious", "Medium", "Medium"
    return "Safe", "Low", "Low"


def clear(db) -> None:
    scans = db["scans"].delete_many({"source": SOURCE}).deleted_count
    alerts = db["alerts"].delete_many({"source": DATASET}).deleted_count
    print(f"removed {scans} EMBER scans and {alerts} EMBER alerts")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill the dashboard with EMBER-2018 samples")
    parser.add_argument("--db", default=None, help="database name override")
    parser.add_argument("--holdout", default=str(BACKEND_ROOT / "app" / "ml" / "ember_holdout.jsonl"))
    parser.add_argument("--alerts", type=int, default=12, help="how many alerts to create")
    parser.add_argument("--days", type=int, default=14, help="spread records across the last N days")
    parser.add_argument("--clear", action="store_true", help="remove EMBER rows and exit")
    args = parser.parse_args()

    load_dotenv(BACKEND_ROOT / ".env")
    url = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI")
    if not url:
        raise SystemExit("MONGODB_URL is not set in backend/.env")

    db_name = args.db or os.getenv("MONGODB_DB_NAME", "sentinelai")
    client = MongoClient(url, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=20000)
    db = client[db_name]
    print(f"database: {db_name}")

    if args.clear:
        clear(db)
        return

    holdout_path = Path(args.holdout)
    if not holdout_path.exists():
        raise SystemExit(f"holdout file missing: {holdout_path} (run train_ember_model.py first)")
    rows = load_holdout(holdout_path)
    if not rows:
        raise SystemExit("holdout file is empty")

    # Replace any previous run, and drop the hand-written demo rows.
    db["scans"].delete_many({"source": SOURCE})
    db["alerts"].delete_many({"source": DATASET})
    removed_demo = db["scans"].delete_many({"seeded": True}).deleted_count
    removed_demo_alerts = db["alerts"].delete_many({"seeded": True}).deleted_count
    print(f"removed demo rows: {removed_demo} scans, {removed_demo_alerts} alerts")

    now = datetime.utcnow()
    scans = []
    for i, row in enumerate(rows):
        verdict, threat_level, severity = severity_for(row)
        family = row.get("family") or None
        sha = row["sha256"]
        label = f"{family}_{sha[:8]}" if family else f"sample_{sha[:8]}"
        # spread newest-first so the dashboard has activity in the last 24h
        created = now - timedelta(hours=(i * 0.7) % (args.days * 24))
        proba = round(float(row["probability"]), 4)
        scans.append(
            {
                "user_id": "ember-benchmark",
                "scan_type": "malware",
                "file_name": f"{label}.exe",
                "file_hash": sha,
                "verdict": verdict,
                "threat_level": threat_level,
                "severity": severity,
                "score": int(round(proba * 100)),
                "result": json.dumps(
                    {
                        "dataset": DATASET,
                        "engine": "ember-lightgbm-v2",
                        "probability": proba,
                        "label": int(row["label"]),
                        "family": family,
                    }
                ),
                "model_probability": proba,
                "malware_probability": proba,
                "ember_label": "malicious" if int(row["label"]) == 1 else "benign",
                "ember_family": family,
                "appeared": row.get("appeared"),
                "dataset": DATASET,
                "source": SOURCE,
                "created_at": created,
            }
        )
    db["scans"].insert_many(scans)
    print(f"inserted {len(scans)} EMBER scans")

    candidates = sorted(
        [s for s in scans if s["verdict"] in ("Malicious", "Suspicious")],
        key=lambda s: s["model_probability"],
        reverse=True,
    )[: args.alerts]

    alerts = []
    for i, scan in enumerate(candidates):
        severity = scan["severity"]
        family = scan.get("ember_family") or "unknown family"
        alerts.append(
            {
                "severity": severity,
                "title": f"EMBER sample detected: {family}",
                "description": (
                    f"{DATASET} benchmark PE {scan['file_hash'][:12]}… classified "
                    f"{scan['verdict'].lower()} with {int(scan['model_probability'] * 100)}% model confidence."
                ),
                "source": DATASET,
                "status": "Open" if i % 3 else "Investigating",
                "created_at": now - timedelta(hours=(i * 3.5) % (args.days * 24)),
                "scan_id": scan["_id"] if "_id" in scan else None,
                "dataset": DATASET,
            }
        )
    # insert_many mutates the source dicts with _id; strip scan_id if unknown
    for alert in alerts:
        alert.pop("scan_id", None)
    if alerts:
        db["alerts"].insert_many(alerts)
    print(f"inserted {len(alerts)} EMBER alerts")
    print("done")


if __name__ == "__main__":
    main()
