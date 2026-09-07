"""LLM Investigation Assistant.
Provides AI-powered natural language reasoning, technical signal translation,
and investigative reporting. Pluggable across OpenAI, Google Gemini, Anthropic,
with resilient zero-crash fallback to the template Explainability Engine.
"""

import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.schemas.analysis import DetectorResult, EvidenceItem, RiskLevel, FraudType
from app.llm.prompts import SYSTEM_INVESTIGATOR_PROMPT, USER_INVESTIGATION_TEMPLATE

logger = logging.getLogger(__name__)


class LLMInvestigator:
    """Configurable LLM provider wrapper for fraud intelligence investigation."""

    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "openai").lower()
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL or "gpt-4o-mini"
        self.enabled = settings.ENABLE_LLM and bool(self.api_key)

    async def generate_investigation_report(
        self,
        input_type: str,
        risk_score: int,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        confidence: float,
        detectors: List[DetectorResult],
        evidence: List[EvidenceItem],
        extracted_content: Dict[str, Any],
        fallback_explanation: str
    ) -> str:
        """Generates an LLM-assisted investigation report, or returns fallback explanation."""
        if not self.enabled or not self.api_key:
            return fallback_explanation

        # Build structured summaries
        det_summary_lines = []
        for d in detectors:
            det_summary_lines.append(
                f"- [{d.module}] Probability: {d.fraud_probability:.2f}, Risk: {d.risk.value}. "
                f"Signals: {', '.join(d.signals) if d.signals else 'None'}"
            )
        detectors_summary = "\n".join(det_summary_lines) or "No detector details available."

        ev_summary_lines = []
        for e in evidence:
            ev_summary_lines.append(
                f"- {e.source_modality} -> [{e.relationship or 'linked_to'}] -> {e.target_modality or 'entity'}: "
                f"{e.content} (Severity: {e.severity})"
            )
        evidence_summary = "\n".join(ev_summary_lines) or "No cross-modal links detected."

        extracted_lines = []
        if extracted_content.get("extracted_urls"):
            extracted_lines.append(f"URLs: {', '.join(extracted_content['extracted_urls'][:5])}")
        if extracted_content.get("extracted_emails"):
            extracted_lines.append(f"Emails: {', '.join(extracted_content['extracted_emails'][:5])}")
        if extracted_content.get("extracted_phones"):
            extracted_lines.append(f"Phones: {', '.join(extracted_content['extracted_phones'][:5])}")
        extracted_summary = "\n".join(extracted_lines) or "No additional entities extracted."

        prompt_content = USER_INVESTIGATION_TEMPLATE.format(
            input_type=input_type,
            risk_score=risk_score,
            risk_level=risk_level.value,
            confidence=confidence,
            fraud_types=", ".join(f.value for f in fraud_types),
            detectors_summary=detectors_summary,
            evidence_summary=evidence_summary,
            extracted_summary=extracted_summary,
        )

        try:
            if self.provider == "openai":
                return await self._call_openai(prompt_content)
            elif self.provider in ("gemini", "google"):
                return await self._call_gemini(prompt_content)
            elif self.provider == "anthropic":
                return await self._call_anthropic(prompt_content)
            else:
                logger.warning(f"Unsupported LLM provider: {self.provider}. Using fallback explanation.")
                return fallback_explanation
        except Exception as e:
            logger.error(f"LLM investigation call failed ({self.provider}): {e}", exc_info=True)
            return fallback_explanation

    async def _call_openai(self, user_content: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_INVESTIGATOR_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()

    async def _call_gemini(self, user_content: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model or "gemini-1.5-flash",
            system_instruction=SYSTEM_INVESTIGATOR_PROMPT,
        )
        resp = await model.generate_content_async(user_content)
        return resp.text.strip()

    async def _call_anthropic(self, user_content: str) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        message = await client.messages.create(
            model=self.model or "claude-3-haiku-20240307",
            max_tokens=600,
            system=SYSTEM_INVESTIGATOR_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return message.content[0].text.strip()
