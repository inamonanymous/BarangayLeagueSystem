from datetime import date

from app.application.common.utils.base_classes import BasePolicy


class TeamPolicy(BasePolicy):
    def normalize_text(self, value: str, field_name: str, max_length: int) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        if not normalized:
            raise ValueError(f"{field_name} is required.")
        if len(normalized) > max_length:
            raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
        return normalized

    def normalize_optional_text(
        self,
        value: str | None,
        field_name: str,
        max_length: int,
    ) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if len(normalized) > max_length:
            raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
        return normalized

    def validate_registration(
        self,
        *,
        season_status: str,
        registration_start_date: date | None,
        registration_end_date: date | None,
        registered_on: date,
    ) -> None:
        if season_status != "REGISTRATION":
            raise ValueError("Teams can only register while the season is in Registration.")
        if (registration_start_date is None) != (registration_end_date is None):
            raise ValueError("Season registration dates must both be set or both be empty.")
        if registration_start_date is not None and registration_end_date is not None:
            if not registration_start_date <= registered_on <= registration_end_date:
                raise ValueError("Team registration is outside the season registration window.")
