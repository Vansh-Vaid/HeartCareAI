from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class HostedLLMProvider:
    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.model = os.environ.get("HEARTCARE_CHATBOT_MODEL", "gpt-4o-mini").strip()
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate(self, question: str, contexts: list[dict[str, Any]]) -> str | None:
        if not self.enabled:
            return None

        context_text = "\n\n".join(
            f"Source: {item['title']} ({item['source']})\n{item['text']}"
            for item in contexts
        )
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a friendly and supportive heart health guide for the HeartCare AI app. "
                        "Your goal is to explain things in simple, easy-to-understand terms. "
                        "If you use medical terms, explain them simply (e.g., instead of 'ischaemia', say 'reduced blood flow'). "
                        "Answer using the provided knowledge base. "
                        "Always be encouraging but remind the user that you are an AI guide, not a doctor, "
                        "and this tool doesn't replace professional medical advice."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nKnowledge base:\n{context_text}",
                },
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            return None
