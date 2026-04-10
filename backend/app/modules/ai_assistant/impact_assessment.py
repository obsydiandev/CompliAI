class ImpactAssessmentGenerator:
    RISK_INDICATORS = {
        "high_risk_keywords": [
            "medical", "healthcare", "diagnostic", "credit", "scoring", "recruitment",
            "autonomous", "vehicle", "biometric", "surveillance", "criminal", "justice",
        ],
        "limited_risk_keywords": ["recommendation", "chatbot", "content"],
        "minimal_risk_keywords": ["spam", "filter", "game"],
    }

    def generate(self, system_data: dict) -> dict:
        general = system_data.get("general_information", {}) or {}
        intended = system_data.get("intended_purpose", {}) or {}
        technical = system_data.get("technical_specifications", {}) or {}

        purpose = str(general.get("purpose", "")).lower()
        use_cases = intended.get("use_cases", [])
        use_cases_str = " ".join(use_cases if isinstance(use_cases, list) else [str(use_cases)]).lower()

        risk_level = self._determine_risk_level(purpose + " " + use_cases_str)

        return {
            "risk_level": risk_level,
            "risk_classification": f"EU AI Act: {risk_level.title()} Risk",
            "affected_populations": self._identify_affected_populations(intended),
            "mitigation_measures": self._generate_mitigations(risk_level, system_data),
            "fundamental_rights_impact": self._assess_fundamental_rights(risk_level),
            "recommended_actions": self._recommend_actions(risk_level),
            "annex_iii_applicable": risk_level == "high",
            "conformity_assessment_required": risk_level == "high",
        }

    def _determine_risk_level(self, text: str) -> str:
        for kw in self.RISK_INDICATORS["high_risk_keywords"]:
            if kw in text:
                return "high"
        for kw in self.RISK_INDICATORS["limited_risk_keywords"]:
            if kw in text:
                return "limited"
        return "minimal"

    def _identify_affected_populations(self, intended: dict) -> list[str]:
        populations = []
        target_users = intended.get("target_users", [])
        if isinstance(target_users, list):
            populations.extend(target_users)
        elif isinstance(target_users, str):
            populations.append(target_users)
        geographic = intended.get("geographic_scope", "")
        if geographic:
            populations.append(f"Users in: {geographic}")
        return populations or ["General public"]

    def _generate_mitigations(self, risk_level: str, system_data: dict) -> list[str]:
        mitigations = [
            "Implement robust human oversight mechanisms",
            "Establish comprehensive logging and audit trails",
            "Conduct regular bias and fairness assessments",
        ]
        if risk_level == "high":
            mitigations.extend([
                "Register system in EU AI Act database",
                "Conduct third-party conformity assessment",
                "Implement fundamental rights impact assessment",
                "Establish quality management system per Annex IX",
            ])
        return mitigations

    def _assess_fundamental_rights(self, risk_level: str) -> dict:
        if risk_level == "high":
            return {
                "privacy": "Significant impact - DPIA required",
                "non_discrimination": "Potential impact - bias testing required",
                "human_dignity": "Monitor for dehumanizing outcomes",
                "due_process": "Ensure right to explanation and appeal",
            }
        return {
            "privacy": "Limited impact",
            "non_discrimination": "Low risk - monitor periodically",
            "human_dignity": "Minimal impact",
            "due_process": "Standard transparency measures sufficient",
        }

    def _recommend_actions(self, risk_level: str) -> list[str]:
        if risk_level == "high":
            return [
                "Complete full Annex IV technical documentation",
                "Conduct conformity assessment",
                "Register in EU AI Act database before deployment",
                "Appoint qualified person responsible for regulatory compliance",
                "Establish post-market monitoring system",
            ]
        return [
            "Complete basic Annex IV documentation",
            "Implement transparency measures",
            "Establish user information procedures",
        ]
