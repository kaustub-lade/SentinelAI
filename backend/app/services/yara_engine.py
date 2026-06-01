"""Simple YARA rule loader and scanner.

This provides minimal safe wrappers so the project can call YARA when
available. If `yara-python` or libyara is not installed the functions
will return empty results instead of raising on import.
"""
import os
from typing import Dict, Any, List, Optional

try:
    import yara
except Exception:  # pragma: no cover - optional dependency
    yara = None


def load_rules(rules_dir: Optional[str] = None) -> Optional[Dict[str, yara.Rules]]:
    """Load all .yar/.yara files from a directory and compile them.

    Returns a dict mapping filename -> compiled rule object or None if
    YARA is unavailable or the directory doesn't exist.
    """
    if yara is None:
        return None

    rules_dir = rules_dir or os.getenv("YARA_RULES_DIR", "./yara_rules")
    if not os.path.isdir(rules_dir):
        return None

    compiled = {}
    for fname in os.listdir(rules_dir):
        if not (fname.endswith(".yar") or fname.endswith(".yara")):
            continue
        path = os.path.join(rules_dir, fname)
        try:
            compiled[fname] = yara.compile(filepath=path)
        except Exception:
            # skip invalid rules but continue loading others
            continue

    return compiled


def scan_bytes(data: bytes, rules: Optional[Dict[str, yara.Rules]] = None) -> Dict[str, Any]:
    """Scan binary `data` with provided compiled rules (or load default).

    Returns a dict with `matches` list.
    """
    if yara is None:
        return {"matches": []}

    if rules is None:
        rules = load_rules()

    if not rules:
        return {"matches": []}

    matches: List[Dict[str, Any]] = []
    for name, compiled in rules.items():
        try:
            m = compiled.match(data=data)
            if m:
                # convert to simple structure
                matches.append({"rule_file": name, "matches": [str(x) for x in m]})
        except Exception:
            continue

    return {"matches": matches}
