from datetime import date

from sqlalchemy.exc import IntegrityError

from app.application.common.utils.base_classes import BaseService
from app.application.season.policies import SeasonConflictError, SeasonPolicy
from app.domain.models.seasons import Season
from app.extensions import db
from app.infrastructure.database.season_repository import SeasonRepository
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class SeasonService(BaseService):
    def __init__(
        self,
        repository: SeasonRepository | None = None,
        policy: SeasonPolicy | None = None,
        unit_of_work: SqlAlchemyUnitOfWork | None = None,
    ) -> None:
        self.repository = repository or SeasonRepository()
        self.policy = policy or SeasonPolicy()
        self.unit_of_work = unit_of_work or SqlAlchemyUnitOfWork()

    def list_seasons(self) -> list[Season]:
        return self.repository.list_all()

    def create_season(
        self,
        *,
        name: str,
        year: int,
        voter_required: bool = False,
        registration_start_date: date | None = None,
        registration_end_date: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Season:
        normalized_name = self.policy.normalize_name(name)
        self.policy.validate_season_details(
            year=year,
            registration_start_date=registration_start_date,
            registration_end_date=registration_end_date,
            start_date=start_date,
            end_date=end_date,
        )

        if self.repository.exists_by_name(normalized_name):
            raise SeasonConflictError("A season with that name already exists.")

        season = Season(
            name=normalized_name,
            year=year,
            voter_required=voter_required,
            registration_start_date=registration_start_date,
            registration_end_date=registration_end_date,
            start_date=start_date,
            end_date=end_date,
            season_status="PLANNING",
        )

        self.repository.add(season)

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise SeasonConflictError(
                "A season with that name already exists or conflicts with existing data."
            ) from exc

        return season

    def update_voter_rule(self, season_id: int, voter_required: bool) -> Season:
        """Change the voter requirement before registration starts."""
        with self.unit_of_work:
            season = self.repository.get_for_update(season_id)
            if season is None:
                raise LookupError("Season not found.")
            if season.season_status != "PLANNING":
                raise ValueError("The voter rule can only be changed during Planning.")
            season.voter_required = voter_required
        return season

    def transition_season(self, season_id: int, next_status: str) -> Season:
        season = self.repository.get_for_update(season_id)
        if season is None:
            raise LookupError("Season not found.")

        normalized_status = self.policy.normalize_status(next_status)
        self.policy.validate_status_transition(season.season_status, normalized_status)
        self.policy.validate_active_season(
            normalized_status,
            self.repository.has_active_season(exclude_id=season.id),
        )
        if normalized_status == "ONGOING":
            if season.voter_required:
                count = self.repository.count_unverified_adults(season.id, season.year, date.today())
                if count:
                    raise SeasonConflictError(
                        f"The season cannot move to Ongoing: {count} adult player(s) need voter verification."
                    )
            incomplete_teams = self.repository.list_teams_below_minimum_roster_size(
                season.id
            )
            if incomplete_teams:
                details = "; ".join(
                    f"{team['team_name']} ({team['division_name']}): "
                    f"{team['roster_count']}/{team['minimum_roster_size']} active players"
                    for team in incomplete_teams
                )
                raise SeasonConflictError(
                    "The season cannot move to Ongoing until every active team meets "
                    f"its division's minimum roster size. Incomplete rosters: {details}."
                )

        season.season_status = normalized_status
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise SeasonConflictError("Season status conflicts with existing data.") from exc

        return season