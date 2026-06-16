from app.core.entities.goal import Goal
from app.core.ports.journal_ports import GoalRepositoryPort


class CreateGoalUseCase:
    def __init__(self, goal_repo: GoalRepositoryPort):
        self.goal_repo = goal_repo

    async def execute(self, user_id: int, goal_name: str, description: str) -> Goal:
        return await self.goal_repo.create(
            user_id=user_id,
            goal_name=goal_name,
            description=description,
        )
