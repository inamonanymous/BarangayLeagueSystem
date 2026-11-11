from sqlalchemy.exc import IntegrityError

from app.application.catalogs.policies import CatalogPolicy
from app.application.common.utils.base_classes import BaseService
from app.domain.models.divisions import Division
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.sports import Sport
from app.extensions import db
from app.infrastructure.database.catalog_repository import CatalogRepository


class CatalogConflictError(ValueError):
    pass


class CatalogService(BaseService):
    def __init__(
        self,
        repository: CatalogRepository | None = None,
        policy: CatalogPolicy | None = None,
    ) -> None:
        self.repository = repository or CatalogRepository()
        self.policy = policy or CatalogPolicy()

    def list_sports(self) -> list[Sport]:
        return self.repository.list_sports()

    def list_divisions(self) -> list[Division]:
        return self.repository.list_divisions()

    def create_sport(self, name: str, description: str | None = None) -> Sport:
        normalized_name = self.policy.normalize_name(name, "Sport")
        normalized_description = self.policy.normalize_description(description)
        if any(sport.name.casefold() == normalized_name.casefold() for sport in self.repository.list_sports()):
            raise CatalogConflictError("A sport with that name already exists.")

        sport = Sport(name=normalized_name, description=normalized_description)
        self.repository.add(sport)
        self._commit("A sport with that name already exists.")
        return sport

    def update_sport(self, sport_id: int, name: str, description: str | None = None) -> Sport:
        sport = self.repository.get_sport(sport_id)
        if sport is None:
            raise LookupError("Sport not found.")
        normalized_name = self.policy.normalize_name(name, "Sport")
        normalized_description = self.policy.normalize_description(description)
        if any(
            existing.id != sport_id and existing.name.casefold() == normalized_name.casefold()
            for existing in self.repository.list_sports()
        ):
            raise CatalogConflictError("A sport with that name already exists.")
        sport.name = normalized_name
        sport.description = normalized_description
        self._commit("A sport with that name already exists.")
        return sport

    def delete_sport(self, sport_id: int) -> None:
        sport = self.repository.get_sport(sport_id)
        if sport is None:
            raise LookupError("Sport not found.")
        if self.repository.sport_is_assigned(sport_id):
            raise CatalogConflictError("This sport is assigned to a season and cannot be deleted.")
        self.repository.delete(sport)
        self._commit("Sport is still referenced and cannot be deleted.")

    def create_division(
        self,
        name: str,
        gender_policy: str,
        minimum_roster_size: int,
        maximum_roster_size: int,
    ) -> Division:
        normalized_name = self.policy.normalize_name(name, "Division")
        normalized_policy = self.policy.validate_division(
            gender_policy,
            minimum_roster_size,
            maximum_roster_size,
        )
        if any(division.name.casefold() == normalized_name.casefold() for division in self.repository.list_divisions()):
            raise CatalogConflictError("A division with that name already exists.")

        division = Division(
            name=normalized_name,
            gender_policy=normalized_policy,
            minimum_roster_size=minimum_roster_size,
            maximum_roster_size=maximum_roster_size,
        )
        self.repository.add(division)
        self._commit("A division with that name already exists.")
        return division

    def update_division(
        self,
        division_id: int,
        name: str,
        gender_policy: str,
        minimum_roster_size: int,
        maximum_roster_size: int,
    ) -> Division:
        division = self.repository.get_division(division_id)
        if division is None:
            raise LookupError("Division not found.")
        normalized_name = self.policy.normalize_name(name, "Division")
        normalized_policy = self.policy.validate_division(
            gender_policy,
            minimum_roster_size,
            maximum_roster_size,
        )
        if any(
            existing.id != division_id and existing.name.casefold() == normalized_name.casefold()
            for existing in self.repository.list_divisions()
        ):
            raise CatalogConflictError("A division with that name already exists.")
        division.name = normalized_name
        division.gender_policy = normalized_policy
        division.minimum_roster_size = minimum_roster_size
        division.maximum_roster_size = maximum_roster_size
        self._commit("A division with that name already exists.")
        return division

    def delete_division(self, division_id: int) -> None:
        division = self.repository.get_division(division_id)
        if division is None:
            raise LookupError("Division not found.")
        if self.repository.division_is_assigned(division_id):
            raise CatalogConflictError("This division is assigned to a season and cannot be deleted.")
        self.repository.delete(division)
        self._commit("Division is still referenced and cannot be deleted.")

    def get_season_configuration(self, season_id: int) -> dict:
        season = self.repository.get_season(season_id)
        if season is None:
            raise LookupError("Season not found.")

        configured_sports = []
        for season_sport in self.repository.season_sports(season_id):
            sport = self.repository.get_sport(season_sport.sport_id)
            configured_divisions = []
            for association in self.repository.season_sport_divisions(season_sport.id):
                division = self.repository.get_division(association.division_id)
                if division is not None:
                    configured_divisions.append(division.to_dict())
            if sport is not None:
                configured_sports.append({
                    **season_sport.to_dict(),
                    "sport": sport.to_dict(),
                    "divisions": configured_divisions,
                })

        return {"season": season.to_dict(), "sports": configured_sports}

    def add_sport_to_season(self, season_id: int, sport_id: int) -> SeasonSport:
        season = self.repository.get_season(season_id)
        if season is None:
            raise LookupError("Season not found.")
        self.policy.validate_season_configurable(season.season_status)

        sport = self.repository.get_sport(sport_id)
        if sport is None:
            raise LookupError("Sport not found.")
        if self.repository.find_season_sport(season_id, sport_id) is not None:
            raise CatalogConflictError("This sport is already assigned to the season.")

        association = SeasonSport(season_id=season_id, sport_id=sport_id)
        self.repository.add(association)
        self._commit("This sport is already assigned to the season.")
        return association

    def add_division_to_season_sport(
        self,
        season_sport_id: int,
        division_id: int,
    ) -> SeasonSportDivision:
        season_sport = self.repository.get_season_sport(season_sport_id)
        if season_sport is None:
            raise LookupError("Season sport assignment not found.")

        season = self.repository.get_season(season_sport.season_id)
        if season is None:
            raise LookupError("Season not found.")
        self.policy.validate_season_configurable(season.season_status)

        division = self.repository.get_division(division_id)
        if division is None:
            raise LookupError("Division not found.")
        if self.repository.division_for_season_sport(season_sport_id, division_id) is not None:
            raise CatalogConflictError("This division is already assigned to the sport in this season.")

        association = SeasonSportDivision(
            season_sport_id=season_sport_id,
            division_id=division_id,
        )
        self.repository.add(association)
        self._commit("This division is already assigned to the sport in this season.")
        return association

    def remove_sport_from_season(self, season_id: int, season_sport_id: int) -> None:
        season = self.repository.get_season(season_id)
        if season is None:
            raise LookupError("Season not found.")
        self.policy.validate_season_configurable(season.season_status)
        association = self.repository.get_season_sport(season_sport_id)
        if association is None or association.season_id != season_id:
            raise LookupError("Sport assignment not found for this season.")
        for division_assignment in self.repository.season_sport_divisions(season_sport_id):
            self.repository.delete(division_assignment)
        self.repository.delete(association)
        self._commit("Sport assignment could not be removed.")

    def remove_division_from_season_sport(
        self,
        season_sport_id: int,
        division_assignment_id: int,
    ) -> None:
        season_sport = self.repository.get_season_sport(season_sport_id)
        if season_sport is None:
            raise LookupError("Season sport assignment not found.")
        season = self.repository.get_season(season_sport.season_id)
        if season is None:
            raise LookupError("Season not found.")
        self.policy.validate_season_configurable(season.season_status)
        assignment = next(
            (
                row for row in self.repository.season_sport_divisions(season_sport_id)
                if row.id == division_assignment_id
            ),
            None,
        )
        if assignment is None:
            raise LookupError("Division assignment not found for this season sport.")
        self.repository.delete(assignment)
        self._commit("Division assignment could not be removed.")

    @staticmethod
    def _commit(conflict_message: str) -> None:
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise CatalogConflictError(conflict_message) from exc