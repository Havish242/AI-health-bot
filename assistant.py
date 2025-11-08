"""
HealthAssistant core logic. This module supports two modes:

- OpenAI-backed chat: if OPENAI_API_KEY is present in the environment and the `openai`
  package is installed, the assistant will call the OpenAI Chat API (gpt-3.5-turbo by default).
- Local rule-based fallback: if no API key is configured or an API call fails, the assistant
  falls back to the original rule-based responses.

Security / safety notes:
- The assistant always includes emergency disclaimers and does not provide personalized
  dosing or definitive medical diagnoses.
"""

from typing import Optional
import os
import logging

try:
    import openai
except Exception:
    openai = None

logger = logging.getLogger(__name__)


class HealthAssistant:
    """A health assistant that prefers an AI model when available.

    Behavior:
    - If OPENAI_API_KEY env var exists and `openai` package is available, use OpenAI Chat API.
    - On any API error or if not configured, return deterministic rule-based replies.
    """

    def __init__(self, name: str = "HealthBot", model: str = "gpt-3.5-turbo"):
        self.name = name
        self.model = model
        self.use_openai = False
        # Public flag indicating whether the last response used OpenAI (True) or rule-based (False).
        self.last_used_openai = False

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and openai is not None:
            try:
                openai.api_key = api_key
                # Basic test: don't call API here, just enable flag
                self.use_openai = True
                logger.info("OpenAI integration enabled for HealthAssistant")
            except Exception:
                logger.exception("Failed to configure OpenAI client; falling back to rule-based assistant")
                self.use_openai = False
        else:
            if api_key and openai is None:
                logger.warning("OPENAI_API_KEY set but openai package is not installed; install openai to enable API mode")

    def _rule_based_respond(self, message: Optional[str]) -> str:
        """Original rule-based logic preserved as a fallback."""
        if not message:
            return (
                "I didn't get your message. Please tell me your symptom or question. "
                "If this is an emergency, call your local emergency number immediately."
            )

        text = message.lower().strip()

        # Emergency patterns
        emergency_terms = (
            "chest pain",
            "difficulty breathing",
            "shortness of breath",
            "severe bleeding",
            "unconscious",
            "not breathing",
            "loss of consciousness",
        )
        for term in emergency_terms:
            if term in text:
                return (
                    f"If you or someone else is experiencing \"{term}\", this may be an emergency. "
                    "Please call your local emergency services (e.g., 911) right away. "
                    "I'm not a substitute for professional medical care."
                )

        # Simple intent handling
        if any(greet in text for greet in ("hi", "hello", "hey", "good morning", "good afternoon")):
            return f"Hello — I'm {self.name}. I can help with general health questions and symptom triage. How can I help you today?"

        if "fever" in text or "temperature" in text:
            return (
                "A fever can be caused by infections. If the fever is high (e.g., above 39°C / 102°F) or persistent, "
                "consider contacting a healthcare provider. Stay hydrated and rest. If you have concerns about a child, elderly person, "
                "or someone with underlying conditions, seek medical advice sooner."
            )

        if any(sym in text for sym in ("cough", "sore throat", "runny nose", "congestion")):
            return (
                "Coughs and colds are commonly viral. Monitor symptoms for worsening (high fever, trouble breathing, confusion). "
                "If symptoms worsen or you are high-risk, contact a clinician. Consider testing for common infections if advised."
            )

        if "headache" in text:
            return (
                "Most headaches are benign. Rest, hydration, and over-the-counter pain relief can help. Seek urgent care if the headache is sudden and severe, "
                "or if it's accompanied by fever, neck stiffness, confusion, or weakness."
            )

        if "medication" in text or "dose" in text or "taking" in text:
            return (
                "I can provide general information about medications, but I can't give personalized dosing or medical advice. "
                "Check the medication leaflet and confirm with your prescriber or pharmacist before changing doses."
            )

        if "appointment" in text or "see a doctor" in text or "visit" in text:
            return (
                "If you need to see a doctor, contact your primary care clinic or an urgent care center. If it's an emergency, call local emergency services. "
                "If you want, tell me your main symptom and I can help suggest whether to see a clinician soon."
            )

        # Default fallback
        return (
            "Thanks for your question. I can help with general symptom information and next-step suggestions, "
            "but I'm not a medical professional. For specific medical advice, please consult your healthcare provider. "
            "Tell me more about your symptoms or ask a specific question (e.g., \"I have a fever and cough\")."
        )

    def _call_openai(self, message: str) -> Optional[str]:
        """Call OpenAI Chat API and return assistant reply or None on failure."""
        if openai is None:
            return None

        try:
            system_prompt = (
                "You are a helpful, safety-conscious health assistant named " + self.name + ". "
                "You provide general medical information and triage suggestions, but always include a clear disclaimer that "
                "you are not a doctor and recommend contacting a healthcare professional for personalized advice. "
                "If a user describes an emergency (chest pain, severe bleeding, difficulty breathing, unconsciousness), "
                "advise them to call local emergency services immediately and do not provide further triage. "
                "Avoid asking for, storing, or processing personally identifiable information."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]

            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=350,
                temperature=0.2,
            )

            # Extract assistant reply
            content = resp.choices[0].message.get("content") if resp.choices else None
            if content:
                return content.strip()
        except Exception:
            logger.exception("OpenAI API call failed")
            return None

        return None

    def respond(self, message: Optional[str], use_openai: Optional[bool] = None) -> str:
        """Return a reply string.

        Parameters:
        - message: user message (str)
        - use_openai: Optional bool to override assistant's configured OpenAI usage for this call.
                      If None, uses the assistant's default `self.use_openai`.

        Side effect: sets `self.last_used_openai` to True/False indicating whether OpenAI produced the reply.
        """
        # Empty input handling still applies
        if not message:
            self.last_used_openai = False
            return self._rule_based_respond(message)

        # decide per-call AI usage
        enabled = self.use_openai if use_openai is None else bool(use_openai)

        # If configured/overridden to use OpenAI, try that first
        if enabled:
            try:
                ai_reply = self._call_openai(message)
                if ai_reply:
                    self.last_used_openai = True
                    return ai_reply
            except Exception:
                logger.exception("Error while using OpenAI; falling back to rule-based reply")

        # Fallback to rule-based answers
        self.last_used_openai = False
        return self._rule_based_respond(message)

