from app.core.entities.journal import Journal
from app.core.ports.journal_ports import GoalRepositoryPort, JournalRepositoryPort


class CreateJournalUseCase:
    def __init__(
        self,
        journal_repo: JournalRepositoryPort,
        goal_repo: GoalRepositoryPort,
    ):
        self.journal_repo = journal_repo
        self.goal_repo = goal_repo

    async def execute(
        self,
        user_id: int,
        goal_id: int,
        study_hours: float,
        today_work: str,
        learning_notes: str,
        challenges: str,
        tomorrow_plan: str,
    ) -> Journal:
        goal = await self.goal_repo.get_by_id_and_user(goal_id, user_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found for user {user_id}")

        return await self.journal_repo.create(
            user_id=user_id,
            goal_id=goal_id,
            study_hours=study_hours,
            today_work=today_work,
            learning_notes=learning_notes,
            challenges=challenges,
            tomorrow_plan=tomorrow_plan,
        )
