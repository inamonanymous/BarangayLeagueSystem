from datetime import date

from app.application.common.utils.base_classes import BasePolicy


class PlayerConflictError(ValueError):
    pass


class PlayerPolicy(BasePolicy):
    def normalize_required(self, value: str, field_name: str, max_length: int) -> str:
        """Trim a required field and enforce its length limit."""
        normalized = value.strip() if isinstance(value, str) else ""
        if not normalized:
            raise ValueError(f"{field_name} is required.")
        if len(normalized) > max_length:
            raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
        return normalized

    def normalize_optional(self, value: str | None, max_length: int = 100) -> str:
        """Normalize an optional middle name to the stored empty-string format."""
        if value is None:
            return ""
        normalized = value.strip()
        if len(normalized) > max_length:
            raise ValueError(f"Optional name must be {max_length} characters or fewer.")
        return normalized

    def validate_birthdate(self, birthdate: date) -> None:
        """Reject birthdates later than today."""
        if birthdate > date.today():
            raise ValueError("Birthdate cannot be in the future.")

    def validate_identity_available(self, exists: bool) -> None:
        """Reject a player identity that already exists, including archived profiles."""
        if exists:
            raise PlayerConflictError("A player with this name and birthdate already exists.")

    def validate_editable(self, is_archived: bool) -> None:
        """Require an archived profile to be restored before editing."""
        if is_archived:
            raise ValueError("Archived player profiles cannot be edited; restore the profile first.")

    @staticmethod
    def is_adult(birthdate: date, on_date: date | None = None) -> bool:
        """Determine whether the player has reached age 18 on the given date."""
        check_date = on_date or date.today()
        age = check_date.year - birthdate.year - (
            (check_date.month, check_date.day) < (birthdate.month, birthdate.day)
        )
        return age >= 18
