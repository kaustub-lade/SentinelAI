import re
from typing import Dict, List


IP_REGEX = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"

URL_REGEX = r"https?://[^\s\"'<>]+"

DOMAIN_REGEX = r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b"

EMAIL_REGEX = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"


def extract_iocs(data: bytes) -> Dict[str, List[str]]:
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = ""

    return {
        "ips": list(set(re.findall(IP_REGEX, text))),
        "urls": list(set(re.findall(URL_REGEX, text))),
        "domains": list(set(re.findall(DOMAIN_REGEX, text))),
        "emails": list(set(re.findall(EMAIL_REGEX, text))),
    }