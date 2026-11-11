from app.application.common.utils.base_classes import BaseService
from app.application.auth.policies import AuthPolicy
from app.domain.models.users import User
from app.infrastructure.database.user_repository import UserRepository


class AuthService(BaseService):
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        policy: AuthPolicy | None = None,
    ) -> None:
        self.user_repository = user_repository or UserRepository()
        self.policy = policy or AuthPolicy()

    def login(self, username: str, password: str):
        user = self.user_repository.get_by_username(username)
        return self.policy.validate_login(user, password)

    def get_current_user(self, user_id: int) -> User | None:
        user = self.user_repository.get_by_id(user_id)
        return user if self.policy.is_active_user(user) else None

    def has_role(self, user: User, role_name: str) -> bool:
        return self.policy.has_role(user, role_name)
