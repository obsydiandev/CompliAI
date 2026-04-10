from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS


class GapAnalyzer:
    def analyze_gaps(self, system_data: dict) -> list[dict]:
        gaps: list[dict] = []

        for section, fields in ANNEX_IV_SECTIONS.items():
            section_data = system_data.get(section, {}) or {}
            for field in fields:
                value = section_data.get(field)
                if value is None or (isinstance(value, str) and value.strip() == "") or (
                    isinstance(value, list) and len(value) == 0
                ):
                    priority = self._get_priority(section, field)
                    gaps.append(
                        {
                            "section": section,
                            "field": field,
                            "priority": priority,
                            "suggestion": self._get_suggestion(section, field),
                        }
                    )
                elif isinstance(value, str) and len(value.strip()) < 30:
                    gaps.append(
                        {
                            "section": section,
                            "field": field,
                            "priority": "low",
                            "suggestion": f"Expand '{field}' with more detailed information for compliance purposes.",
                        }
                    )

        return gaps

    def _get_priority(self, section: str, field: str) -> str:
        high_priority_sections = {"general_information", "intended_purpose", "technical_specifications"}
        medium_priority_sections = {"training_data", "testing_and_validation", "human_oversight"}
        if section in high_priority_sections:
            return "high"
        if section in medium_priority_sections:
            return "medium"
        return "low"

    def _get_suggestion(self, section: str, field: str) -> str:
        suggestions = {
            "system_name": "Provide the official name of the AI system as it will appear in regulatory filings.",
            "purpose": "Describe the primary purpose and intended function of the AI system.",
            "model_architecture": "Specify the ML algorithm type, model size, and key architectural choices.",
            "data_sources": "List all data sources used for training, including origin, size, and collection method.",
            "oversight_mechanisms": "Describe how humans will monitor and control the AI system's operation.",
            "security_measures": "Detail the technical and organizational security measures implemented.",
            "monitoring_plan": "Define how the system will be monitored post-deployment for performance and safety.",
        }
        return suggestions.get(field, f"Complete the '{field}' field with relevant information for EU AI Act compliance.")
