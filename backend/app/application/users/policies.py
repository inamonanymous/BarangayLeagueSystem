from app.application.common.utils.base_classes import BasePolicy


class UserPolicy(BasePolicy):
    def normalize_username(self, username: str) -> str:
        normalized_username = username.strip() if isinstance(username, str) else ""
        if not 3 <= len(normalized_username) <= 100:
            raise ValueError("Username must be between 3 and 100 characters.")
        return normalized_username

    def validate_password(self, password: str) -> None:
        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            raise ValueError("Password must be between 8 and 128 characters.")