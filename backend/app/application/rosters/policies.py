from app.application.common.utils.base_classes import BasePolicy


class RosterPolicy(BasePolicy):
    def normalize_jersey_number(self, jersey_number: str) -> str:
        normalized = jersey_number.strip() if isinstance(jersey_number, str) else ""
        if not normalized:
            raise ValueError("Jersey number is required.")
        if len(normalized) > 10:
            raise ValueError("Jersey number must be 10 characters or fewer.")
        return normalized

    def validate_roster_capacity(self, current_size: int, maximum_size: int) -> None:
        if current_size >= maximum_size:
            raise ValueError("The team roster is already at its maximum size.")
