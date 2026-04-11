"""Lite-specific PDF builder for the Quick-Start Wizard (Epic 0).

Key differences from the Pro PDF (pdf.py):
- Mandatory DRAFT watermark "DRAFT – requires legal review" (not removable)
- Mandatory disclaimer section before content (non-skippable)
- Optional logo upload (partner/user logo)
- Optional partner branding ("Prepared by [Partner Name]")
- CompliAI branding hidden when partner_name is set

Per PRD v1.15 §1.4 and Closed Decisions:
- Watermark is architectural — not a configuration option
- Disclaimer checkbox verified server-side (disclaimer_accepted must be True)
"""

from __future__ import annotations

import hashlib
from datetime import date


DISCLAIMER_TEXT = (
    "Technical File Completion % means structural completeness only — this document "
    "was generated on the basis of information provided by the system owner and has "
    "not been independently verified. It requires review by a qualified legal "
    "professional and the ML Lead before submission to any supervisory authority. "
    "CompliAI provides a documentation tool, not legal advice."
)

WATERMARK_TEXT = "DRAFT – requires legal review"

PDF_WIZARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  @page {
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {
      content: "{{ footer_text }} | {{ gen_date }}";
      font-size: 8pt;
      color: #888;
    }
    @top-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8pt;
      color: #888;
    }
    background-image: url("data:image/svg+xml,{{ watermark_svg }}");
  }
  body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 10pt;
    color: #222;
    line-height: 1.6;
  }
  .watermark {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-45deg);
    font-size: 64pt;
    color: rgba(239, 68, 68, 0.08);
    font-weight: bold;
    white-space: nowrap;
    pointer-events: none;
    z-index: -1;
  }
  .cover {
    text-align: center;
    padding-top: 3cm;
    page-break-after: always;
  }
  .cover .logo-area { margin-bottom: 1cm; }
  .cover .logo-area img { max-height: 80px; max-width: 240px; }
  .cover .logo-text { font-size: 26pt; font-weight: bold; color: #1a56db; }
  .cover .subtitle { font-size: 13pt; color: #555; margin-top: 0.4cm; }
  .cover .meta table { margin: 1.5cm auto 0; border-collapse: collapse; }
  .cover .meta td { padding: 5px 14px; }
  .cover .meta .label { font-weight: bold; color: #555; }
  .cover .draft-badge {
    display: inline-block;
    margin-top: 1.2cm;
    padding: 8px 20px;
    background: #fef3c7;
    color: #92400e;
    border: 2px solid #f59e0b;
    border-radius: 6px;
    font-size: 11pt;
    font-weight: bold;
    letter-spacing: 1px;
  }
  .disclaimer-box {
    border: 2px solid #ef4444;
    background: #fff7f7;
    border-radius: 6px;
    padding: 14px 18px;
    margin: 0.6cm 0 1cm;
    page-break-inside: avoid;
  }
  .disclaimer-box .disclaimer-title {
    font-weight: bold;
    color: #b91c1c;
    font-size: 10pt;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .disclaimer-box p { margin: 0; font-size: 9pt; color: #374151; line-height: 1.5; }
  h1 { font-size: 16pt; color: #1a56db; border-bottom: 2px solid #1a56db;
       padding-bottom: 4px; margin-top: 0.8cm; }
  h2 { font-size: 12pt; color: #1e40af; margin-top: 0.5cm; }
  .section-block { page-break-inside: avoid; margin-bottom: 1cm; }
  .section-header {
    background: #eff6ff;
    border-left: 4px solid #1a56db;
    padding: 6px 12px;
    margin-bottom: 8px;
  }
  .section-header h2 { font-size: 12pt; margin: 0; color: #1e40af; }
  .section-body { white-space: pre-wrap; font-size: 10pt; color: #111; line-height: 1.6; }
  .placeholder { color: #d1d5db; font-style: italic; }
  .completion-bar-bg { background: #e5e7eb; height: 6px; border-radius: 3px; width: 100%; margin-top: 4px; }
  .completion-bar-fill { height: 6px; border-radius: 3px; background: #10b981; }
  .prepared-by { margin-top: 1cm; font-size: 9pt; color: #6b7280; }
</style>
</head>
<body>

<div class="watermark">{{ watermark_text }}</div>

<!-- Cover page -->
<div class="cover">
  <div class="logo-area">
    {% if logo_data_uri %}
    <img src="{{ logo_data_uri }}" alt="Logo"/>
    {% else %}
    <div class="logo-text">{{ display_name }}</div>
    {% endif %}
  </div>
  <div class="subtitle">EU AI Act — Annex IV Technical File</div>
  <div class="meta">
    <table>
      {% if org_name %}<tr><td class="label">Organisation</td><td>{{ org_name }}</td></tr>{% endif %}
      <tr><td class="label">AI System</td><td>{{ system_name }}</td></tr>
      <tr><td class="label">Generated</td><td>{{ gen_date }}</td></tr>
      {% if doc_hash %}<tr><td class="label">Document ID</td><td>{{ doc_hash }}</td></tr>{% endif %}
    </table>
    <div class="draft-badge">DRAFT – requires legal review</div>
  </div>
</div>

<!-- Disclaimer — mandatory, not removable -->
<div class="disclaimer-box">
  <div class="disclaimer-title">⚠ Important Notice</div>
  <p>{{ disclaimer_text }}</p>
</div>

<!-- Table of contents -->
<h1>Table of Contents</h1>
<ul>
  {% for section in toc %}
  <li><a href="#section-{{ section.id }}">{{ section.label }}</a></li>
  {% endfor %}
</ul>

<!-- Sections -->
{% for section in sections %}
<div class="section-block" id="section-{{ section.id }}">
  <div class="section-header">
    <h2>{{ section.label }}</h2>
  </div>
  {% if section.text %}
  <div class="section-body">{{ section.text }}</div>
  {% else %}
  <div class="section-body placeholder">[Section not completed — please fill in during review]</div>
  {% endif %}
</div>
{% endfor %}

{% if partner_name %}
<div class="prepared-by">Prepared by {{ partner_name }}</div>
{% endif %}

</body>
</html>
"""


def build_lite_pdf(
    session,
    disclaimer_accepted: bool,
    logo_bytes: bytes | None = None,
    logo_mime: str | None = None,
    partner_name: str | None = None,
) -> bytes:
    """Generate a Lite Wizard PDF.

    Args:
        session: WizardSession ORM instance
        disclaimer_accepted: MUST be True — enforced server-side
        logo_bytes: optional raw logo image bytes
        logo_mime: MIME type of logo (e.g. 'image/png')
        partner_name: if set, show "Prepared by [partner]" and hide CompliAI branding

    Raises:
        ValueError: if disclaimer_accepted is False (non-skippable per PRD v1.15)

    Returns:
        PDF bytes
    """
    if not disclaimer_accepted:
        raise ValueError(
            "Disclaimer must be accepted before exporting. "
            "This is a non-skippable requirement per EU AI Act documentation standards."
        )

    from jinja2 import BaseLoader, Environment
    from weasyprint import HTML

    paragraphs: dict = session.generated_paragraphs or {}
    org_name: str = session.org_name or ""
    system_name: str = session.system_name or "AI System"
    gen_date = date.today().isoformat()

    # Build a stable doc hash for traceability
    doc_hash = hashlib.sha256(
        f"{session.session_token}:{gen_date}".encode()
    ).hexdigest()[:16]

    # Logo as data URI
    logo_data_uri: str | None = None
    if logo_bytes and logo_mime:
        import base64
        logo_data_uri = f"data:{logo_mime};base64,{base64.b64encode(logo_bytes).decode()}"

    # Section mapping: block_id → Annex IV section label
    SECTION_MAP = [
        {"id": "B1", "label": "Section 1: General Description and Intended Purpose"},
        {"id": "B2", "label": "Section 2–3: System Architecture and Training Data"},
        {"id": "B3", "label": "Section 4: Validation, Accuracy and Testing"},
        {"id": "B4", "label": "Section 6: Risk Management"},
        {"id": "B5", "label": "Section 5: Monitoring, Operation and Human Oversight"},
        {"id": "B6", "label": "Section 7: Post-Market Monitoring"},
        {"id": "B7", "label": "Section 8–9: Standards, Norms and Declaration of Conformity"},
    ]

    sections = [
        {
            "id": s["id"],
            "label": s["label"],
            "text": paragraphs.get(s["id"], ""),
        }
        for s in SECTION_MAP
    ]

    display_name = partner_name or "CompliAI"
    footer_text = f"Prepared by {partner_name}" if partner_name else "Generated by CompliAI"

    ctx = {
        "org_name": org_name,
        "system_name": system_name,
        "gen_date": gen_date,
        "doc_hash": doc_hash,
        "disclaimer_text": DISCLAIMER_TEXT,
        "watermark_text": WATERMARK_TEXT,
        "watermark_svg": "",
        "logo_data_uri": logo_data_uri,
        "display_name": display_name,
        "footer_text": footer_text,
        "partner_name": partner_name,
        "toc": [{"id": s["id"], "label": s["label"]} for s in SECTION_MAP],
        "sections": sections,
    }

    env = Environment(loader=BaseLoader())
    template = env.from_string(PDF_WIZARD_TEMPLATE)
    html_content = template.render(**ctx)
    return HTML(string=html_content).write_pdf()
