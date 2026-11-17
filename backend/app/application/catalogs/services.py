from sqlalchemy.exc import IntegrityError

from app.application.catalogs.policies import CatalogPolicy
from app.application.common.utils.base_classes import BaseService
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.extensions import db
from app.infrastructure.database.catalog_repository import CatalogRepository


class CatalogConflictError(ValueError):
    pass


class CatalogService(BaseService):
    def __init__(self, repository: CatalogRepository | None = None, policy: CatalogPolicy | None = None) -> None:
        self.repository = repository or CatalogRepository()
        self.policy = policy or CatalogPolicy()

    def get_season_configuration(self, season_id: int) -> dict:
        season = self.repository.get_season(season_id)
        if season is None:
            raise LookupError("Season not found.")
        return {
            "season": season.to_dict(),
            "sports": [
                {**sport.to_dict(), "divisions": [
                    division.to_dict() for division in self.repository.season_sport_divisions(sport.id)
                ]}
                for sport in self.repository.season_sports(season_id)
            ],
        }

    def create_sport(self, season_id: int, *, name: str, description: str | None = None) -> SeasonSport:
        self._validate_season(season_id)
        name = self.policy.normalize_name(name, "Sport")
        description = self.policy.normalize_description(description)
        if self.repository.sport_name_exists(season_id, name):
            raise CatalogConflictError("A sport with that name already exists in this season.")
        sport = SeasonSport(season_id=season_id, name=name, description=description)
        self.repository.add(sport)
        self._commit("Sport could not be saved because of a database constraint.")
        return sport

    def update_sport(self, season_id: int, sport_id: int, *, name: str, description: str | None = None) -> SeasonSport:
        self._validate_season(season_id)
        sport = self._get_sport(season_id, sport_id)
        name = self.policy.normalize_name(name, "Sport")
        description = self.policy.normalize_description(description)
        if self.repository.sport_name_exists(season_id, name, exclude_id=sport_id):
            raise CatalogConflictError("A sport with that name already exists in this season.")
        sport.name, sport.description = name, description
        self._commit("Sport could not be saved because of a database constraint.")
        return sport

    def create_division(
        self, sport_id: int, *, name: str, minimum_roster_size: int,
        maximum_roster_size: int, gender_policy: str = "ANY",
    ) -> SeasonSportDivision:
        sport = self._get_configurable_sport(sport_id)
        name, gender_policy = self._normalize_division(name, gender_policy, minimum_roster_size, maximum_roster_size)
        if self.repository.division_name_exists(sport.id, name):
            raise CatalogConflictError("A division with that name already exists in this sport.")
        division = SeasonSportDivision(
            season_sport_id=sport.id, name=name, gender_policy=gender_policy,
            minimum_roster_size=minimum_roster_size, maximum_roster_size=maximum_roster_size,
        )
        self.repository.add(division)
        self._commit("Division could not be saved because of a database constraint.")
        return division

    def update_division(
        self, sport_id: int, division_id: int, *, name: str, minimum_roster_size: int,
        maximum_roster_size: int, gender_policy: str = "ANY",
    ) -> SeasonSportDivision:
        sport = self._get_configurable_sport(sport_id)
        division = self.repository.get_division(division_id)
        if division is None or division.season_sport_id != sport.id:
            raise LookupError("Division not found for this season sport.")
        name, gender_policy = self._normalize_division(name, gender_policy, minimum_roster_size, maximum_roster_size)
        if self.repository.division_name_exists(sport.id, name, exclude_id=division_id):
            raise CatalogConflictError("A division with that name already exists in this sport.")
        division.name = name
        division.gender_policy = gender_policy
        division.minimum_roster_size = minimum_roster_size
        division.maximum_roster_size = maximum_roster_size
        self._commit("Division could not be saved because of a database constraint.")
        return division

    def remove_sport_from_season(self, season_id: int, sport_id: int) -> None:
        self._validate_season(season_id)
        sport = self._get_sport(season_id, sport_id)
        divisions = self.repository.season_sport_divisions(sport.id)
        if any(self.repository.division_assignment_has_teams(division.id) for division in divisions):
            raise CatalogConflictError("This sport has registered teams and cannot be removed from the season.")
        for division in divisions:
            self.repository.delete(division)
        self.repository.remove_sport_statistics(sport.id)
        self.repository.delete(sport)
        self._commit("Sport could not be removed.")

    def remove_division_from_season_sport(self, sport_id: int, division_id: int) -> None:
        self._get_configurable_sport(sport_id)
        division = self.repository.get_division(division_id)
        if division is None or division.season_sport_id != sport_id:
            raise LookupError("Division not found for this season sport.")
        if self.repository.division_assignment_has_teams(division.id):
            raise CatalogConflictError("This division has registered teams and cannot be removed from the season.")
        self.repository.delete(division)
        self._commit("Division could not be removed.")

    def _validate_season(self, season_id: int) -> None:
        season = self.repository.get_season(season_id)
        if season is None:
            raise LookupError("Season not found.")
        self.policy.validate_season_configurable(season.season_status)

    def _get_sport(self, season_id: int, sport_id: int) -> SeasonSport:
        sport = self.repository.get_season_sport(sport_id)
        if sport is None or sport.season_id != season_id:
            raise LookupError("Sport not found for this season.")
        return sport

    def _get_configurable_sport(self, sport_id: int) -> SeasonSport:
        sport = self.repository.get_season_sport(sport_id)
        if sport is None:
            raise LookupError("Season sport not found.")
        self._validate_season(sport.season_id)
        return sport

    def _normalize_division(self, name: str, gender_policy: str, minimum: int, maximum: int) -> tuple[str, str]:
        return self.policy.normalize_name(name, "Division"), self.policy.validate_division(gender_policy, minimum, maximum)

    @staticmethod
    def _commit(conflict_message: str) -> None:
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise CatalogConflictError(conflict_message) from exc
