"""
ISO 42001 crosswalk mapping EU AI Act Annex IV sections to ISO/IEC 42001:2023 clauses.

ISO 42001 clause reference:
  4.1 - Understanding the organization and its context
  4.2 - Understanding the needs and expectations of interested parties
  5.1 - Leadership and commitment
  5.3 - Organizational roles, responsibilities and authorities
  6.1 - Actions to address risks and opportunities
  6.2 - AI objectives and planning to achieve them
  7.4 - Communication
  8.3 - AI system impact assessment
  8.4 - AI system development
  8.5 - AI system operation
  9.1 - Monitoring, measurement, analysis and evaluation
  9.2 - Internal audit
  9.3 - Management review
  10.2 - Continual improvement
"""

CROSSWALK: dict[str, list[str]] = {
    "general_information": ["4.1", "4.2", "5.1"],
    "intended_purpose": ["4.1", "4.2", "6.1"],
    "technical_specifications": ["6.1", "6.2", "8.4"],
    "training_data": ["6.1", "8.3", "8.4"],
    "testing_and_validation": ["6.1", "8.4", "9.1"],
    "human_oversight": ["5.3", "6.2", "8.5"],
    "cybersecurity": ["6.2", "8.5", "9.3"],
    "transparency": ["4.2", "7.4", "8.5"],
    "post_market_monitoring": ["9.1", "9.2", "10.2"],
}


def get_crosswalk(section: str) -> list[str]:
    return CROSSWALK.get(section, [])


def get_full_crosswalk() -> dict:
    return CROSSWALK
