"""PDF and CSV portfolio report generation."""
import io
from datetime import datetime


def generate_portfolio_pdf(org_data: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    org_name = org_data.get("name", "Organization")
    story.append(Paragraph(f"CompliAI Portfolio Report: {org_name}", styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    systems = org_data.get("systems", [])
    story.append(Paragraph(f"AI Systems: {len(systems)}", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))

    if systems:
        table_data = [["System Name", "Version", "Risk Level", "Status", "Completeness %"]]
        for sys in systems:
            completeness = sys.get("completeness_pct", 0)
            table_data.append([
                sys.get("name", ""),
                sys.get("version", ""),
                sys.get("risk_level", ""),
                sys.get("status", ""),
                f"{completeness:.1f}%",
            ])
        table = Table(table_data, colWidths=[2 * inch, 1 * inch, 1.2 * inch, 1 * inch, 1.2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)

    doc.build(story)
    return buffer.getvalue()


def generate_portfolio_csv(org_data: dict) -> str:
    import pandas as pd

    systems = org_data.get("systems", [])
    if not systems:
        return "name,version,risk_level,status,completeness_pct\n"

    rows = []
    for sys in systems:
        rows.append({
            "name": sys.get("name", ""),
            "version": sys.get("version", ""),
            "risk_level": sys.get("risk_level", ""),
            "status": sys.get("status", ""),
            "completeness_pct": sys.get("completeness_pct", 0),
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)
