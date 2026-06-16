import json
import logging
import os
import re

import httpx

from app.core.ports.repository_ports import RepositoryAnalysisResult, RepositoryAnalyzerPort

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a senior software architect.

You MUST return ONLY valid JSON.

Do not explain.
Do not add markdown.
Do not add code fences.
Do not echo repository contents."""

USER_PROMPT = """This repository is a {project_type} project named {repo_name}.

Analyze the repository for security, performance, maintainability, architecture, and scalability.

Return JSON matching exactly this schema:
{{
"overall_score": 0,
"security_score": 0,
"performance_score": 0,
"maintainability_score": 0,
"architecture_score": 0,
"strengths": [],
"weaknesses": [],
"recommendations": []
}}

All scores must be floats from 0 to 100.

Repository Context:
{repo_context}"""

FALLBACK_ANALYSIS = RepositoryAnalysisResult(
    overall_score=50.0,
    security_score=50.0,
    performance_score=50.0,
    maintainability_score=50.0,
    architecture_score=50.0,
    strengths=[],
    weaknesses=["LLM parsing failed"],
    recommendations=["Retry analysis"],
)


class GroqRepositoryAnalyzer(RepositoryAnalyzerPort):
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

    async def analyze(
        self, repo_name: str, project_type: str, context: str
    ) -> RepositoryAnalysisResult:
        user_prompt = USER_PROMPT.format(
            repo_name=repo_name,
            project_type=project_type,
            repo_context=context,
        )
        response_text = await self._call_groq(user_prompt)
        return self._parse_response(response_text)

    async def _call_groq(self, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},
        }

        logger.info("[RepositoryAnalysis] Calling Groq API model=%s", self.model)
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(GROQ_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Groq repository analysis API error: %s", exc.response.text)
            raise RuntimeError("Repository analysis service unavailable") from exc
        except httpx.RequestError as exc:
            logger.error("Groq repository analysis request failed: %s", exc)
            raise RuntimeError("Repository analysis service unavailable") from exc

        logger.info("[RepositoryAnalysis] Groq response received")
        return data["choices"][0]["message"]["content"]

    def _parse_response(self, response_text: str) -> RepositoryAnalysisResult:
        logger.info("[RepositoryAnalysis] Raw LLM response:\n%s", response_text)

        parsed = self._try_parse_json(response_text)
        if parsed is None:
            logger.warning(
                "[RepositoryAnalysis] Failed to parse Groq response; using fallback analysis"
            )
            return FALLBACK_ANALYSIS

        logger.info("[RepositoryAnalysis] JSON parsed successfully")
        return self._to_result(parsed)

    def _try_parse_json(self, response_text: str) -> dict | None:
        candidates = [
            response_text.strip(),
            self._extract_fenced_json(response_text),
            self._extract_first_json_object(response_text),
        ]

        for candidate in candidates:
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        return None

    def _extract_fenced_json(self, text: str) -> str | None:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_first_json_object(self, text: str) -> str | None:
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False

        for index in range(start, len(text)):
            char = text[index]

            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]

        return None

    def _to_result(self, parsed: dict) -> RepositoryAnalysisResult:
        try:
            return RepositoryAnalysisResult(
                overall_score=float(parsed["overall_score"]),
                security_score=float(parsed["security_score"]),
                performance_score=float(parsed["performance_score"]),
                maintainability_score=float(parsed["maintainability_score"]),
                architecture_score=float(parsed["architecture_score"]),
                strengths=[str(item) for item in parsed.get("strengths", [])],
                weaknesses=[str(item) for item in parsed.get("weaknesses", [])],
                recommendations=[str(item) for item in parsed.get("recommendations", [])],
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "[RepositoryAnalysis] Parsed JSON missing required fields: %s", exc
            )
            return FALLBACK_ANALYSIS
