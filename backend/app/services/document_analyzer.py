import re


def analyze_document(content: bytes):

    text = content.decode(
        "utf-8",
        errors="ignore"
    )

    urls = [
    url.rstrip(").,]")
    for url in re.findall(
        r'https?://[^\s"\'>]+',
        text
    )
]

    suspicious_keywords = [
        "powershell",
        "cmd.exe",
        "javascript",
        "vbscript",
        "macro",
        "download",
        "payload",
        "shellcode",
        "exploit",
    ]

    detected = []

    lower_text = text.lower()

    for keyword in suspicious_keywords:
        if keyword in lower_text:
            detected.append(keyword)

    score = min(
        len(detected) * 0.15,
        1.0
    )
    print("\nDOCUMENT ANALYSIS:")
    print("URLs:", len(urls))
    print("Keywords:", detected)
    print()

    return {
        "document_type": "document",
        "urls": urls,
        "suspicious_keywords": detected,
        "risk_score": score,
        "verdict": (
            "suspicious"
            if score >= 0.5
            else "benign"
        ),
    }