from app.application.common.utils.base_classes import BasePolicy
from app.domain.models.users import User


class AuthPolicy(BasePolicy):
    def validate_login(self, user: User | None, password: str) -> User:
        if user is None or not user.verify_password(password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is inactive")
        return user

    def is_active_user(self, user: User | None) -> bool:
        return user is not None and user.is_active

    def has_role(self, user: User, role_name: str) -> bool:
        return user.role == role_name