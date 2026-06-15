def generate_incident_summary(scan_result: dict) -> str:

    verdict = scan_result.get(
        "verdict",
        "Unknown"
    )

    entropy = (
        scan_result
        .get("behavioral_indicators", {})
        .get("entropy", 0)
    )

    packed = (
        scan_result
        .get("behavioral_indicators", {})
        .get("packed", False)
    )

    mitre = (
        scan_result
        .get("mitre_techniques", [])
    )

    vt = (
        scan_result
        .get("virustotal", {})
    )

    malicious = vt.get(
        "malicious",
        0
    )

    suspicious = vt.get(
        "suspicious",
        0
    )

    sections = []

    # -------------------------
    # Risk Assessment
    # -------------------------

    sections.append(
        f"Risk Assessment: {verdict}"
    )

    # -------------------------
    # Behavioral Analysis
    # -------------------------

    behavior = []

    if packed:
        behavior.append(
            "Packed or obfuscated executable detected."
        )

    if entropy >= 7:
        behavior.append(
            f"High entropy observed ({entropy:.2f}), "
            "which may indicate packing, encryption, "
            "or anti-analysis techniques."
        )

    if not behavior:
        behavior.append(
            "No significant behavioral anomalies "
            "were identified during static analysis."
        )

    sections.append(
        "\nBehavioral Analysis:\n• "
        + "\n• ".join(behavior)
    )

    # -------------------------
    # MITRE ATT&CK
    # -------------------------

    if mitre:

        mitre_lines = []

        for technique in mitre[:3]:

            mitre_lines.append(
                f"{technique.get('technique_id')} - "
                f"{technique.get('technique_name')}"
            )

        sections.append(
            "\nMITRE ATT&CK Findings:\n• "
            + "\n• ".join(mitre_lines)
        )

    else:

        sections.append(
            "\nMITRE ATT&CK Findings:\n"
            "• No mapped ATT&CK techniques identified."
        )

    # -------------------------
    # Threat Intelligence
    # -------------------------

    if malicious > 0:

        sections.append(
            f"\nThreat Intelligence:\n"
            f"• VirusTotal reported "
            f"{malicious} malicious detections "
            f"across security vendors."
        )

    elif suspicious > 0:

        sections.append(
            f"\nThreat Intelligence:\n"
            f"• VirusTotal reported "
            f"{suspicious} suspicious detections."
        )

    else:

        sections.append(
            "\nThreat Intelligence:\n"
            "• No malicious detections were reported "
            "by VirusTotal."
        )

    # -------------------------
    # Recommended Actions
    # -------------------------

    if verdict.lower() == "malicious":

        action = (
            "Immediately isolate the file, "
            "perform containment procedures, "
            "and investigate potentially affected systems."
        )

    elif verdict.lower() == "suspicious":

        action = (
            "Perform dynamic sandbox analysis, "
            "monitor endpoint activity, and "
            "validate file legitimacy before execution."
        )

    else:

        action = (
            "No immediate threat indicators detected. "
            "Continue standard monitoring procedures."
        )

    sections.append(
        f"\nRecommended Action:\n• {action}"
    )

    return "\n".join(sections)