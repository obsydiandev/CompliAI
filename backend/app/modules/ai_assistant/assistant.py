import logging

from app.config import settings

logger = logging.getLogger(__name__)


class AIAssistant:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self._client = None

    def _get_client(self):
        if not self.api_key:
            return None
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                return None
        return self._client

    def suggest_section(self, system_data: dict, section: str) -> str:
        client = self._get_client()
        if client is None:
            return f"AI suggestions unavailable. Please configure OPENAI_API_KEY. Section: {section}"

        system_name = (system_data.get("general_information") or {}).get("system_name", "AI System")
        prompt = (
            f"You are an EU AI Act compliance expert. For the AI system named '{system_name}', "
            f"generate high-quality Annex IV technical documentation content for the section: '{section}'. "
            f"Existing system context: {system_data}. "
            f"Provide concise, professional content suitable for regulatory compliance documentation."
        )
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("OpenAI suggest_section error: %s", e)
            return f"AI suggestion failed: {e}"

    def review_document(self, system_data: dict) -> dict:
        client = self._get_client()
        if client is None:
            return {
                "status": "unavailable",
                "message": "AI review unavailable. Please configure OPENAI_API_KEY.",
                "recommendations": [],
            }

        prompt = (
            "You are an EU AI Act compliance expert. Review the following Annex IV technical documentation "
            f"and provide a structured compliance assessment: {system_data}. "
            "Return a JSON object with keys: overall_quality (1-10), strengths (list), weaknesses (list), "
            "recommendations (list), compliance_readiness (percentage)."
        )
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
            )
            content = response.choices[0].message.content or "{}"
            import json
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"status": "ok", "raw_review": content, "recommendations": []}
        except Exception as e:
            logger.error("OpenAI review_document error: %s", e)
            return {"status": "error", "message": str(e), "recommendations": []}
