from datetime import date

from app.application.common.utils.base_classes import BasePolicy


SEASON_STATUSES = {"PLANNING", "REGISTRATION", "ONGOING", "COMPLETED", "ARCHIVED"}
ACTIVE_SEASON_STATUSES = {"REGISTRATION", "ONGOING"}
SEASON_STATUS_TRANSITIONS = {
    "PLANNING": {"REGISTRATION", "ARCHIVED"},
    "REGISTRATION": {"ONGOING", "ARCHIVED"},
    "ONGOING": {"COMPLETED"},
    "COMPLETED": {"ARCHIVED"},
    "ARCHIVED": set(),
}


class SeasonConflictError(ValueError):
    pass


class SeasonPolicy(BasePolicy):
    def normalize_name(self, name: str) -> str:
        normalized_name = name.strip() if isinstance(name, str) else ""
        if not normalized_name:
            raise ValueError("Season name is required.")
        if len(normalized_name) > 100:
            raise ValueError("Season name must be 100 characters or fewer.")
        return normalized_name

    def normalize_status(self, season_status: str) -> str:
        normalized_status = season_status.strip().upper() if isinstance(season_status, str) else ""
        if normalized_status not in SEASON_STATUSES:
            raise ValueError("Season status is not supported.")
        return normalized_status

    def validate_season_details(
        self,
        *,
        year: int,
        registration_start_date: date | None,
        registration_end_date: date | None,
        start_date: date | None,
        end_date: date | None,
    ) -> None:
        if isinstance(year, bool) or not isinstance(year, int) or year < 1:
            raise ValueError("Season year must be a positive integer.")
        if (registration_start_date is None) != (registration_end_date is None):
            raise ValueError("Provide both registration dates or leave both empty.")
        if registration_start_date is not None and not isinstance(registration_start_date, date):
            raise ValueError("Registration start date must be a date.")
        if registration_end_date is not None and not isinstance(registration_end_date, date):
            raise ValueError("Registration end date must be a date.")
        if registration_start_date is not None and registration_end_date is not None and registration_start_date > registration_end_date:
            raise ValueError("Registration start date must be on or before its end date.")
        if start_date is not None and not isinstance(start_date, date):
            raise ValueError("Season start date must be a date.")
        if end_date is not None and not isinstance(end_date, date):
            raise ValueError("Season end date must be a date.")
        if end_date is not None and start_date is None:
            raise ValueError("Season start date is required when an end date is provided.")
        if (
            start_date is not None
            and registration_end_date is not None
            and start_date < registration_end_date
        ):
            raise ValueError("Season start date must be on or after registration ends.")
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("Season start date must be on or before its end date.")

    def validate_active_season(self, season_status: str, has_active_season: bool) -> None:
        if season_status in ACTIVE_SEASON_STATUSES and has_active_season:
            raise SeasonConflictError("Another season is already active.")

    def validate_status_transition(self, current_status: str, next_status: str) -> None:
        if next_status not in SEASON_STATUS_TRANSITIONS.get(current_status, set()):
            raise ValueError(
                f"Season cannot transition from {current_status} to {next_status}."
            )