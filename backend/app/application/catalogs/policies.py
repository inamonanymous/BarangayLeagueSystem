from app.application.common.utils.base_classes import BasePolicy


class CatalogPolicy(BasePolicy):
    GENDER_POLICIES = {"ANY", "MALE_ONLY", "FEMALE_ONLY", "MIXED"}

    def normalize_name(self, name: str, entity_name: str) -> str:
        normalized = name.strip() if isinstance(name, str) else ""
        if not normalized:
            raise ValueError(f"{entity_name} name is required.")
        if len(normalized) > 100:
            raise ValueError(f"{entity_name} name must be 100 characters or fewer.")
        return normalized

    def normalize_description(self, description: str | None) -> str | None:
        if description is None:
            return None
        if not isinstance(description, str):
            raise ValueError("Description must be text.")
        normalized = description.strip()
        return normalized or None

    def validate_division(
        self,
        gender_policy: str,
        minimum_roster_size: int,
        maximum_roster_size: int,
    ) -> str:
        normalized_policy = gender_policy.strip().upper() if isinstance(gender_policy, str) else ""
        if normalized_policy not in self.GENDER_POLICIES:
            raise ValueError("Gender policy is not supported.")
        if isinstance(minimum_roster_size, bool) or not isinstance(minimum_roster_size, int) or minimum_roster_size < 1:
            raise ValueError("Minimum roster size must be a positive integer.")
        if isinstance(maximum_roster_size, bool) or not isinstance(maximum_roster_size, int):
            raise ValueError("Maximum roster size must be an integer.")
        if maximum_roster_size < minimum_roster_size:
            raise ValueError("Maximum roster size must be at least the minimum roster size.")
        return normalized_policy

    def validate_season_configurable(self, season_status: str) -> None:
        if season_status not in {"PLANNING", "REGISTRATION"}:
            raise ValueError("Season sports and divisions can only be configured while the season is Planning or Registration.")