"""LLM provider abstraction with Google Gemini support and zero-key Mock fallback."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, Iterator, Optional

logger = logging.getLogger(__name__)

CAREERPILOT_SYSTEM_INSTRUCTION = """You are CareerPilot, a professional personal career guide and co-pilot for college students.
STRICT GUIDELINES:
1. Conversational Context Gathering: You are a professional career guide. Naturally ask the user about their branch, year of study, and career goals conversationally. Once you have enough context, recommend they try one of the platform features: ATS Resume Check, 90-Day Roadmap, Job Matches, or Mock Interview.
2. Language: Communicate strictly in clear, professional English at all times.
3. Length Budget: Strictly keep your responses concise, between 2 to 3 short lines (maximum 3 concise sentences). Never exceed 3 sentences.
4. Tone: Be encouraging, empathetic, and solution-oriented. Never judge the student by their college tier, backlogs, marks, or CGPA.
5. Actionability: Focus on practical skills, real-world projects, and concrete next steps."""


@dataclass
class LLMResponse:
    text: str
    usage: Optional[Dict[str, float]] = None


class MockLLMProvider:
    """Deterministic zero-key LLM provider ensuring immediate out-of-the-box operation."""

    name = "MockDeterministicProvider"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        text = self._craft_contextual_reply(prompt, system_prompt)
        return LLMResponse(
            text=text,
            usage={"promptTokens": 42, "completionTokens": 28, "costUsd": 0.0},
        )

    def generate_stream(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        full_text = self._craft_contextual_reply(prompt, system_prompt)
        words = full_text.split(" ")
        for idx, word in enumerate(words):
            yield ("" if idx == 0 else " ") + word

    @staticmethod
    def _craft_contextual_reply(prompt: str, system_prompt: Optional[str] = None) -> str:
        lower = prompt.lower()
        if any(k in lower for k in ("resume", "ats", "cv")):
            return (
                "Let's sharpen your resume for ATS filters! Open the ATS Resume Review tool to get your "
                "100-point rubric breakdown and 3 concrete before-and-after bullet rewrites."
            )
        if any(k in lower for k in ("roadmap", "plan", "90", "learn", "syllabus")):
            return (
                "A structured 90-day sequence will keep your prep focused on real projects. "
                "Tap 90-Day Roadmap below to generate your 12-week plan with vetted free resources."
            )
        if any(k in lower for k in ("job", "intern", "hiring", "apply", "placement")):
            return (
                "We rank fresher openings purely on your skills—never your college tier or CGPA. "
                "Tap Matched Jobs below to inspect verified roles and scam-shielded listings."
            )
        if any(k in lower for k in ("interview", "mock", "hr", "practice")):
            return (
                "Practicing out loud builds real interview confidence! Launch the 5-Min Mock Interview "
                "to answer role-specific questions and get a 4-pillar score report."
            )
        if system_prompt and "Branch:" in system_prompt and "Unknown" not in system_prompt:
            return (
                "Got your profile context! Let's turn your current skills into placement readiness—"
                "pick ATS Resume Review, 90-Day Roadmap, Matched Jobs, or Mock Interview below."
            )
        return (
            "I'm CareerPilot, your personal career guide! Tell me your branch, year, and target role, "
            "or launch one of the 4 core career tools below to get started."
        )


class GeminiProvider:
    """Google GenAI SDK adapter with automatic graceful fallback to MockLLMProvider."""

    name = "GeminiProvider"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        fallback_to_mock: bool = True,
    ) -> None:
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model_name = model_name
        self.fallback_to_mock = fallback_to_mock
        self._client = None
        if self.api_key:
            try:
                from google import genai  # type: ignore

                self._client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                logger.warning("Failed to initialize google-genai client: %s", exc)
                self._client = None

    def _candidate_models(self) -> list[str]:
        if "pro" in self.model_name:
            return ["gemini-2.5-pro", "gemini-2.5-flash"]
        return [self.model_name, "gemini-2.5-flash", "gemini-2.0-flash"]

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self._client:
            return MockLLMProvider().generate_text(prompt, system_prompt)

        instruction = (
            f"{CAREERPILOT_SYSTEM_INSTRUCTION}\n\n[Task Context]:\n{system_prompt}"
            if system_prompt
            else CAREERPILOT_SYSTEM_INSTRUCTION
        )
        for model in self._candidate_models():
            try:
                from google.genai import types  # type: ignore

                response = self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=instruction,
                        temperature=0.6,
                        max_output_tokens=180,
                    ),
                )
                text = (response.text or "").strip()
                if text:
                    return LLMResponse(text=text)
            except Exception as exc:
                logger.warning("Gemini model %s failed: %s", model, exc)

        if self.fallback_to_mock:
            return MockLLMProvider().generate_text(prompt, system_prompt)
        raise RuntimeError("All Gemini models failed.")

    def generate_stream(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        if not self._client:
            yield from MockLLMProvider().generate_stream(prompt, system_prompt)
            return

        instruction = (
            f"{CAREERPILOT_SYSTEM_INSTRUCTION}\n\n[Task Context]:\n{system_prompt}"
            if system_prompt
            else CAREERPILOT_SYSTEM_INSTRUCTION
        )
        for model in self._candidate_models():
            try:
                from google.genai import types  # type: ignore

                yielded = False
                for chunk in self._client.models.generate_content_stream(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=instruction,
                        temperature=0.6,
                        max_output_tokens=180,
                    ),
                ):
                    text = getattr(chunk, "text", None)
                    if text:
                        yielded = True
                        yield text
                if yielded:
                    return
            except Exception as exc:
                logger.warning("Gemini stream model %s failed: %s", model, exc)

        if self.fallback_to_mock:
            yield from MockLLMProvider().generate_stream(prompt, system_prompt)
            return
        raise RuntimeError("All Gemini streaming models failed.")


def get_active_llm_provider(task: str = "chat"):
    """Return GeminiProvider when GEMINI_API_KEY is configured, else MockLLMProvider."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        model_name = "gemini-2.5-pro" if task == "heavy" else "gemini-2.5-flash"
        return GeminiProvider(api_key=api_key, model_name=model_name)
    return MockLLMProvider()
