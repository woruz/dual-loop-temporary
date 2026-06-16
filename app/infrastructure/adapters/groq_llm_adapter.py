import json
import logging
import os
import re

import httpx

from app.core.entities.goal import Goal
from app.core.entities.journal import Journal
from app.core.ports.journal_ports import JournalAnalysisResult, JournalLLMPort

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqLLMAdapter(JournalLLMPort):
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

    async def analyze_journal(self, goal: Goal, journal: Journal) -> JournalAnalysisResult:
        prompt = self._build_prompt(goal, journal)
        response_text = await self._call_groq(prompt)
        return self._parse_response(response_text)

    def _build_prompt(self, goal: Goal, journal: Journal) -> str:
        return f"""You are an expert productivity coach analyzing a daily study journal.

Goal: {goal.goal_name}
Goal Description: {goal.description}

Journal Entry:
- Study Hours: {journal.study_hours}
- Today's Work: {journal.today_work}
- Learning Notes: {journal.learning_notes}
- Challenges: {journal.challenges}
- Tomorrow's Plan: {journal.tomorrow_plan}

Analyze this journal entry and respond with ONLY valid JSON (no markdown fences) using this exact schema:
{{
  "productivity_score": <float 0-100>,
  "sentiment_score": <float 0-100>,
  "goal_alignment_score": <float 0-100>,
  "risk_level": "<low|medium|high>",
  "feedback": "<constructive feedback paragraph>"
}}

Scoring guide:
- productivity_score: how effectively study time was used
- sentiment_score: overall emotional tone and motivation
- goal_alignment_score: how well today's work advances the stated goal
- risk_level: likelihood of falling behind on the goal (low/medium/high)
"""

    async def _call_groq(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(GROQ_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Groq API error: %s", exc.response.text)
            raise RuntimeError("Journal analysis service unavailable") from exc
        except httpx.RequestError as exc:
            logger.error("Groq request failed: %s", exc)
            raise RuntimeError("Journal analysis service unavailable") from exc

        return data["choices"][0]["message"]["content"]

    def _parse_response(self, response_text: str) -> JournalAnalysisResult:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Groq response: %s", response_text)
            raise ValueError("LLM returned invalid JSON") from exc

        risk_level = str(parsed.get("risk_level", "medium")).lower()
        if risk_level not in ("low", "medium", "high"):
            risk_level = "medium"

        return JournalAnalysisResult(
            productivity_score=float(parsed["productivity_score"]),
            sentiment_score=float(parsed["sentiment_score"]),
            goal_alignment_score=float(parsed["goal_alignment_score"]),
            risk_level=risk_level,
            feedback=str(parsed["feedback"]),
        )
