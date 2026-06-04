from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet


def generate_malware_pdf(scan: dict) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("SentinelAI Malware Analysis Report", styles["Title"])
    )

    mitre = scan.get("mitre_techniques", [])

    if mitre:
        elements.append(
            Paragraph("MITRE ATT&CK Techniques", styles["Heading2"])
        )

        for tech in mitre:
            elements.append(
                Paragraph(
                    f"{tech.get('technique_id')} - {tech.get('technique_name', '')}",
                    styles["BodyText"]
                )
            )

        elements.append(Spacer(1, 12))

    vt = scan.get("virustotal", {})

    if vt:
        elements.append(
            Paragraph("VirusTotal Intelligence", styles["Heading2"])
        )

        for key, value in vt.items():
            elements.append(
                Paragraph(
                    f"{key}: {value}",
                    styles["BodyText"]
                )
            )

        elements.append(Spacer(1, 12))

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph("File Information", styles["Heading2"])
    )

    elements.append(
        Paragraph(f"File Name: {scan.get('file_name')}", styles["BodyText"])
    )

    elements.append(
        Paragraph(f"SHA256: {scan.get('file_hash')}", styles["BodyText"])
    )

    elements.append(
        Paragraph(f"File Size: {scan.get('file_size')} bytes", styles["BodyText"])
    )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph("Analysis Results", styles["Heading2"])
    )

    elements.append(
        Paragraph(f"Verdict: {scan.get('verdict')}", styles["BodyText"])
    )

    elements.append(
        Paragraph(f"Threat Level: {scan.get('threat_level')}", styles["BodyText"])
    )

    elements.append(
        Paragraph(
            f"Malware Probability: {scan.get('malware_probability')}",
            styles["BodyText"]
        )
    )

    elements.append(Spacer(1, 12))

    elements.append(
    Paragraph("Behavioral Indicators", styles["Heading2"])
    )
    behavior = scan.get("behavioral_indicators", {})

    for key, value in behavior.items():
        elements.append(
            Paragraph(
                f"{key}: {value}",
                styles["BodyText"]
            )
        )

    elements.append(Spacer(1, 12))

    elements.append(
    Paragraph("Indicators of Compromise (IOCs)", styles["Heading2"])
)

    iocs = scan.get("iocs", {})

    for category, values in iocs.items():

        elements.append(
            Paragraph(
                f"{category.upper()}",
                styles["Heading3"]
            )
        )

        if values:
            for value in values:
                elements.append(
                    Paragraph(
                        str(value),
                        styles["BodyText"]
                    )
                )
        else:
            elements.append(
                Paragraph(
                    "None Detected",
                    styles["BodyText"]
                )
            )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph("Recommendations", styles["Heading2"])
    )

    for rec in scan.get("recommendations", []):
        elements.append(
            Paragraph(f"• {rec}", styles["BodyText"])
        )

    doc.build(elements)

    buffer.seek(0)

    return buffer

