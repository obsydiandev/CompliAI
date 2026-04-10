"""PDF export utilities."""
import io


def export_system_pdf(system_data: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    general = system_data.get("general_information", {}) or {}
    name = general.get("system_name", "AI System")
    story.append(Paragraph(f"Annex IV Technical Documentation: {name}", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    for section, data in system_data.items():
        if isinstance(data, dict):
            story.append(Paragraph(section.replace("_", " ").title(), styles["Heading2"]))
            for field, value in data.items():
                if value:
                    story.append(Paragraph(f"<b>{field}:</b> {value}", styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return buffer.getvalue()
