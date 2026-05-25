import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMClient:
    api_key: str
    model: str = "gpt-4o-mini"

    def generate_plan(self, prompt: str) -> str | None:
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return only valid JSON. Do not generate SQL.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError):
            return None

        return payload["choices"][0]["message"]["content"]


def get_llm_client() -> LLMClient | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    return LLMClient(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
