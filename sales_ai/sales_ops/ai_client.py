from __future__ import annotations

import os
from typing import Optional


class AIMessageGenerator:
    def __init__(self) -> None:
        self.provider = "fallback"
        self.model = None
        self._client = None
        self._types = None

        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if gemini_key:
            try:
                from google import genai
                from google.genai import types

                self._client = genai.Client(api_key=gemini_key)
                self._types = types
                self.provider = "gemini"
                self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                return
            except Exception:
                self._client = None

        if openai_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=openai_key)
                self.provider = "openai"
                self.model = os.getenv("OPENAI_MODEL", "gpt-5.4")
            except Exception:
                self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def generate(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self._client:
            return None

        if self.provider == "gemini":
            return self._generate_gemini(system_prompt, user_prompt)
        if self.provider == "openai":
            return self._generate_openai(system_prompt, user_prompt)
        return None

    def _generate_gemini(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=self._types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            text = getattr(response, "text", None)
            return text.strip() if text else None
        except Exception:
            return None

    def _generate_openai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
                ],
            )

            text = getattr(response, "output_text", None)
            if text:
                return text.strip()

            output = getattr(response, "output", None) or []
            chunks: list[str] = []
            for item in output:
                for content in getattr(item, "content", []) or []:
                    candidate = getattr(content, "text", None)
                    if candidate:
                        chunks.append(candidate)

            return "\n".join(chunks).strip() or None
        except Exception:
            return None
