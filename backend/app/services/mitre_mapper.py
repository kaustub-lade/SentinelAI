"""MITRE ATT&CK mapping helpers.

This module provides a lightweight mapping from extracted features to
MITRE ATT&CK techniques. For demo purposes it contains a small heuristic
mapping and can optionally load the official MITRE enterprise JSON to
provide richer technique metadata if present at `MITRE_DATA_PATH`.
"""
import json
import os
from typing import Dict, List, Any

MITRE_DATA_PATH = os.getenv(
    "MITRE_DATA_PATH",
    "app/data/enterprise-attack.json"
)


def load_mitre_data(path: str = MITRE_DATA_PATH) -> Dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


# Simple heuristic mapping: keywords -> ATT&CK technique IDs (examples)
HEURISTIC_MAP = {
    "CreateProcess": ["T1059"],  # command and scripting interpreter
    "WS2_32.dll": ["T1043"],
    "upx": ["T1027"],  # obfuscated or packed files
    "powershell": ["T1059.001"],
    "cmd.exe": ["T1059.003"],
    "rundll32": ["T1218"],

    "RegSetValue": ["T1112"],
    "RegCreateKey": ["T1112"],
    "RegOpenKey": ["T1112"],

    "WriteProcessMemory": ["T1055"],
    "CreateRemoteThread": ["T1055"],
    "VirtualAllocEx": ["T1055"],

    "URLDownloadToFile": ["T1105"],
    "WinHttpOpen": ["T1071"],
    "InternetOpen": ["T1071"],
    "InternetConnect": ["T1071"],

    "socket": ["T1071"],
    "connect": ["T1071"],

    "GetAsyncKeyState": ["T1056"],
    "SetWindowsHookEx": ["T1056"],

    "CreateService": ["T1543"],
    "OpenSCManager": ["T1543"],

    "TaskScheduler": ["T1053"],
    "schtasks": ["T1053"],

    "lsass": ["T1003"],
    "MiniDumpWriteDump": ["T1003"],

    "net user": ["T1136"],
    "net localgroup": ["T1098"],

    "certutil": ["T1140"],
    "bitsadmin": ["T1197"],

    "wmic": ["T1047"],
}


_MITRE_DATA = load_mitre_data()


def map_features(features: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return a list of matched MITRE techniques (id, name) based on features.

    Uses heuristic map plus optional MITRE data if available.
    """
    detected: List[Dict[str, str]] = []

    # check section names
    sections = features.get("pe", {}).get("sections", []) or []
    for sec in sections:
        lower = sec.lower()
        for key, tt in HEURISTIC_MAP.items():
            if key.lower() in lower:
                for tid in tt:
                    detected.append({"technique_id": tid, "source": "heuristic"})

    # check imports
    imports = features.get("pe", {}).get("imports", {}) or {}
    for dll, funcs in imports.items():
        for key, tt in HEURISTIC_MAP.items():
            if key.lower() in dll.lower() or any(key.lower() in (f or "").lower() for f in funcs):
                for tid in tt:
                    detected.append({"technique_id": tid, "source": "heuristic"})

    # simple check for packed/high-entropy
    if features.get("high_entropy") or features.get("suspected_packed"):
        for tid in HEURISTIC_MAP.get("upx", []):
            detected.append({"technique_id": tid, "source": "heuristic"})

    # canonicalize and attach names if MITRE data present
    if _MITRE_DATA and "objects" in _MITRE_DATA:
        tech_index = {}
        for obj in _MITRE_DATA.get("objects", []):
            if obj.get("type") == "attack-pattern":
                tid = obj.get("external_references", [{}])[0].get("external_id")
                if tid:
                    tech_index[tid] = obj.get("name")

        for d in detected:
            tid = d.get("technique_id")
            if tid in tech_index:
                d["technique_name"] = tech_index[tid]

    # deduplicate by technique_id
    uniq: Dict[str, Dict[str, str]] = {}
    for item in detected:
        tid = item.get("technique_id")
        if tid and tid not in uniq:
            uniq[tid] = item

    return list(uniq.values())
