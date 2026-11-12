from datetime import date

from app.application.common.utils.base_classes import BasePolicy


class PlayerPolicy(BasePolicy):
    def normalize_required(self, value: str, field_name: str, max_length: int) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        if not normalized:
            raise ValueError(f"{field_name} is required.")
        if len(normalized) > max_length:
            raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
        return normalized

    def normalize_optional(self, value: str | None, max_length: int = 100) -> str:
        if value is None:
            return ""
        normalized = value.strip()
        if len(normalized) > max_length:
            raise ValueError(f"Optional name must be {max_length} characters or fewer.")
        return normalized

    def validate_birthdate(self, birthdate: date) -> None:
        if birthdate > date.today():
            raise ValueError("Birthdate cannot be in the future.")

    @staticmethod
    def is_adult(birthdate: date, on_date: date | None = None) -> bool:
        check_date = on_date or date.today()
        age = check_date.year - birthdate.year - (
            (check_date.month, check_date.day) < (birthdate.month, birthdate.day)
        )
        return age >= 18
