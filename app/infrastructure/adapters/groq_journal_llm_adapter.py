import os
import json
import logging
from typing import Optional
import httpx
from app.core.entities.journal import Journal
from app.core.ports.journal_llm import JournalLLMPort, JournalAnalysisResult

logger = logging.getLogger("app.infrastructure.adapters.groq_journal_llm_adapter")

class GroqJournalLLMAdapter(JournalLLMPort):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not self.api_key:
            logger.warning(
                "SECURITY/INTEGRATION WARNING: GROQ_API_KEY environment variable is not set. "
                "The GroqJournalLLMAdapter will run in fallback simulation mode."
            )
        else:
            logger.info(f"GroqJournalLLMAdapter initialized with model '{self.model}'")

    async def analyze_journal(
        self,
        user_goal: str,
        user_experience: str,
        journal: Journal,
        commits: list[dict]
    ) -> JournalAnalysisResult:
        logger.info(f"Starting analysis for journal '{journal.id}'")

        # Fetch commit details and git diffs from GitHub API
        git_activity_str = await self._fetch_git_activity_details(commits)

        if not self.api_key:
            logger.info("GROQ_API_KEY not found. Using local fallback analysis simulation.")
            return self._generate_fallback_analysis(user_goal, user_experience, journal, git_activity_str)

        system_instruction = (
            "You are a professional software engineering mentor and productivity assistant.\n"
            "Analyze the developer's daily journal entry and their Git activity (commits and diffs) "
            "against their professional experience and goal.\n"
            "You MUST respond ONLY with a JSON object. Do not include any explanation outside the JSON.\n"
            "JSON structure:\n"
            "{\n"
            "  \"productivity_score\": float (0.0 to 10.0 representing efficiency/completion of work),\n"
            "  \"sentiment_score\": float (0.0 to 10.0 representing morale/stress levels based on notes and challenges),\n"
            "  \"goal_alignment_score\": float (0.0 to 10.0 representing how well today's work aligns with the stated goal),\n"
            "  \"risk_level\": string (either \"low\", \"medium\", or \"high\"),\n"
            "  \"missing_goal\": string (markdown text, detailing what goals, sub-goals, or critical components are missing, neglected, or not worked on today in comparison to their overarching goal),\n"
            "  \"match_goal\": string (markdown text, detailing what aspects of today's work and code diffs aligned, matched, or directly contributed towards their overarching goal),\n"
            "  \"recommendation\": string (markdown text, providing concrete next steps and actionable mentor recommendations for tomorrow)\n"
            "}"
        )

        user_content = (
            f"Developer Goal: {user_goal or 'Not set'}\n"
            f"Developer Experience: {user_experience or 'Not set'}\n\n"
            f"--- Daily Journal ---\n"
            f"Study Hours: {journal.study_hours}\n"
            f"Today's Work: {journal.today_work}\n"
            f"Learning Notes: {journal.learning_notes}\n"
            f"Challenges: {journal.challenges}\n\n"
            f"--- Git Activity (Commits & Code Diffs) ---\n"
            f"{git_activity_str}\n"
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_content}
                        ],
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Groq API returned error status {response.status_code}: {response.text}")
                    return self._generate_fallback_analysis(user_goal, user_experience, journal, git_activity_str)

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                result = json.loads(content)
                logger.info(f"Groq analysis completed successfully for journal '{journal.id}'")
                
                return JournalAnalysisResult(
                    productivity_score=float(result.get("productivity_score", 7.0)),
                    sentiment_score=float(result.get("sentiment_score", 7.0)),
                    goal_alignment_score=float(result.get("goal_alignment_score", 7.0)),
                    risk_level=str(result.get("risk_level", "low")).lower(),
                    missing_goal=str(result.get("missing_goal", "Not analyzed.")),
                    match_goal=str(result.get("match_goal", "Not analyzed.")),
                    recommendation=str(result.get("recommendation", "No recommendation provided."))
                )

        except Exception as e:
            logger.exception(f"Unexpected error communicating with Groq API: {e}. Falling back to simulation.")
            return self._generate_fallback_analysis(user_goal, user_experience, journal, git_activity_str)

    async def _fetch_git_activity_details(self, commits: list[dict]) -> str:
        """
        Fetches modified files and patch diffs from GitHub API for the commits list.
        """
        git_details = []
        for c in commits:
            repo_name = c.get("repo_name")
            branch = c.get("branch")
            
            for sha, msg in c.get("message", {}).items():
                diff_text = ""
                modified_files = []
                try:
                    headers = {"User-Agent": "Dual-Loop-App"}
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        url = f"https://api.github.com/repos/{repo_name}/commits/{sha}"
                        res = await client.get(url, headers=headers)
                        if res.status_code == 200:
                            data = res.json()
                            for f in data.get("files", []):
                                filename = f.get("filename")
                                additions = f.get("additions", 0)
                                deletions = f.get("deletions", 0)
                                modified_files.append(f"{filename} (+{additions}, -{deletions})")
                                
                                patch = f.get("patch", "")
                                if patch:
                                    diff_text += f"\nFile {filename}:\n{patch[:800]}"
                except Exception as ex:
                    logger.warning(f"Failed to fetch commit details for {repo_name} @ {sha} from GitHub: {ex}")

                commit_detail = (
                    f"- **Repo:** {repo_name}\n"
                    f"  **Branch:** {branch}\n"
                    f"  **Commit:** `{sha[:8]}`\n"
                    f"  **Message:** {msg}\n"
                )
                if modified_files:
                    commit_detail += f"  **Files:** {', '.join(modified_files)}\n"
                if diff_text:
                    commit_detail += f"  **Diff patches:**\n```diff{diff_text}\n```\n"
                git_details.append(commit_detail)

        return "\n".join(git_details) if git_details else "No commits pushed today."

    def _generate_fallback_analysis(
        self,
        user_goal: str,
        user_experience: str,
        journal: Journal,
        git_activity_str: str
    ) -> JournalAnalysisResult:
        """
        Generates simulated scores and constructive feedback as a robust fallback.
        """
        prod_score = min(max(journal.study_hours * 1.5, 3.0), 9.5)
        
        lower_challenges = journal.challenges.lower()
        if "stuck" in lower_challenges or "failed" in lower_challenges or "error" in lower_challenges:
            sent_score = 6.0
            risk = "medium"
        elif not journal.challenges.strip() or "none" in lower_challenges:
            sent_score = 9.5
            risk = "low"
        else:
            sent_score = 8.0
            risk = "low"

        goal_align = 8.0
        goal_matched = False
        if user_goal:
            goal_words = set(user_goal.lower().split())
            work_words = set(journal.today_work.lower().split())
            matches = goal_words.intersection(work_words)
            if matches:
                goal_align = 9.0
                goal_matched = True
            else:
                goal_align = 7.0

        # Create split simulated response feedback
        missing_goal_sim = (
            f"You spent `{journal.study_hours}` hours today. "
            f"However, we did not detect deep coverage on specific long-term sub-goals related to *\"{user_goal or 'your stated focus'}\"*. "
            "Ensure you allocate structured sessions for architectural reviews and unit test mappings."
        )

        if goal_matched:
            match_goal_sim = (
                f"Great alignment! Your work on *\"{journal.today_work}\"* directly matched "
                f"your overarching goal: *\"{user_goal}\"*."
            )
        else:
            match_goal_sim = (
                f"You completed tasks related to: *\"{journal.today_work}\"*. "
                f"While valuable, try to focus more directly on mapping these tasks back to your primary goal: *\"{user_goal or 'Not set'}\"*."
            )

        recommendation_sim = (
            f"1. **Isolate Blockers:** You reported the challenge: *\"{journal.challenges}\"*. Tomorrow, dedicate the first 45 minutes to debugging this blocker.\n"
            f"2. **Track Metrics:** Aim to match your study velocity of `{journal.study_hours}` hours.\n"
            "3. **Refactor Code:** Focus on clean decoupling of adapters."
        )

        return JournalAnalysisResult(
            productivity_score=prod_score,
            sentiment_score=sent_score,
            goal_alignment_score=goal_align,
            risk_level=risk,
            missing_goal=missing_goal_sim,
            match_goal=match_goal_sim,
            recommendation=recommendation_sim
        )
