import re
import ipaddress
from typing import Dict, List


# -------------------------
# Regex Patterns
# -------------------------

IP_REGEX = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"

URL_REGEX = (
    r"https?://"
    r"[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+"
)

DOMAIN_REGEX = (
    r"\b(?:[a-z0-9]"
    r"(?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,}\b"
)

EMAIL_REGEX = (
    r"\b[a-zA-Z0-9._%+-]+@"
    r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
)

# Extract printable strings from binaries
STRING_REGEX = r"[ -~]{4,}"


# -------------------------
# Valid TLDs
# -------------------------

VALID_TLDS = {
    "com",
    "org",
    "net",
    "io",
    "gov",
    "edu",
    "co",
    "uk",
    "in",
    "de",
    "fr",
    "jp",
    "au",
    "cn",
    "ru",
    "xyz",
    "info",
    "biz",
}


# -------------------------
# False-positive domains
# -------------------------

IGNORE_DOMAINS = {
    "sklearn.tree",
    "sklearn.ensemble",
    "numpy.random",
    "numpy.core",
    "numpy.linalg",
    "pandas.core",
    "joblib.numpy_pickle",
    "scipy.stats",
    "scipy.sparse",
}


# -------------------------
# IOC Extraction
# -------------------------

def extract_iocs(data: bytes) -> Dict[str, List[str]]:

    try:
        raw_text = data.decode(
            "utf-8",
            errors="ignore"
        )
    except Exception:
        raw_text = ""

    # ---------------------------------
    # Extract printable strings only
    # ---------------------------------

    strings = re.findall(
        STRING_REGEX,
        raw_text
    )

    text = "\n".join(strings)

    # ---------------------------------
    # Raw Extraction
    # ---------------------------------

    ips = list(
        set(
            re.findall(IP_REGEX, text)
        )
    )

    urls = list(
        set(
            re.findall(URL_REGEX, text)
        )
    )

    domains = list(
        set(
            re.findall(DOMAIN_REGEX, text)
        )
    )

    emails = list(
        set(
            re.findall(EMAIL_REGEX, text)
        )
    )

    # ---------------------------------
    # IP Validation
    # ---------------------------------

    valid_ips = []

    for ip in ips:
        try:
            ip_obj = ipaddress.ip_address(ip)

            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            ):
                continue

            first_octet = int(ip.split(".")[0])

            if first_octet < 10:
                continue

            valid_ips.append(ip)

        except Exception:
            pass

    # ---------------------------------
    # Domain Filtering
    # ---------------------------------

    filtered_domains = []

    for domain in domains:

        domain = domain.lower()

        if domain in IGNORE_DOMAINS:
            continue

        if len(domain) < 6:
            continue

        if not (1 <= domain.count(".") <= 4):
            continue

        tld = domain.split(".")[-1]

        if tld not in VALID_TLDS:
            continue

        filtered_domains.append(domain)

    # ---------------------------------
    # Email Filtering
    # ---------------------------------

    filtered_emails = []

    for email in emails:

        if len(email) < 6:
            continue

        try:

            domain_part = email.split("@")[1]

            tld = domain_part.split(".")[-1]

            if tld not in VALID_TLDS:
                continue

            filtered_emails.append(email)

        except Exception:
            pass

    # ---------------------------------
    # URL Filtering
    # ---------------------------------

    filtered_urls = []

    for url in urls:

        if not url.startswith(
            ("http://", "https://")
        ):
            continue

        if len(url) < 10:
            continue

        # Drop certificate blob junk
        if len(url) > 200:
            continue

        # Common PE certificate artifacts
        if "ocsp.digicert.com0" in url:
            continue

        if ".crt0" in url:
            continue

        if ".crl0" in url:
            continue

        filtered_urls.append(url)

    # ---------------------------------
    # Final Result
    # ---------------------------------

    return {
        "ips": sorted(
            set(valid_ips)
        )[:20],

        "urls": sorted(
            set(filtered_urls)
        )[:20],

        "domains": sorted(
            set(filtered_domains)
        )[:20],

        "emails": sorted(
            set(filtered_emails)
        )[:20],
    }