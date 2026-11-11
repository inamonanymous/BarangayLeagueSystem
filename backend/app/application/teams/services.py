from datetime import date, datetime

from sqlalchemy.exc import IntegrityError

from app.application.common.utils.base_classes import BaseService
from app.application.teams.policies import TeamPolicy
from app.domain.models.season_teams import SeasonTeam
from app.extensions import db
from app.infrastructure.database.season_team_repository import SeasonTeamRepository


class SeasonTeamConflictError(ValueError):
    pass


class SeasonTeamService(BaseService):
    def __init__(
        self,
        repository: SeasonTeamRepository | None = None,
        policy: TeamPolicy | None = None,
    ) -> None:
        self.repository = repository or SeasonTeamRepository()
        self.policy = policy or TeamPolicy()

    def list_for_division(self, assignment_id: int) -> list[SeasonTeam]:
        if self.repository.get_division_assignment(assignment_id) is None:
            raise LookupError("Season division assignment not found.")
        return self.repository.list_for_division(assignment_id)

    def update_team(
        self,
        team_id: int,
        *,
        name: str,
        barangay: str,
        coach_name: str | None = None,
        manager_name: str | None = None,
        team_color: str | None = None,
    ) -> SeasonTeam:
        team = self.repository.get_team(team_id)
        if team is None:
            raise LookupError("Team not found.")
        if team.is_archived:
            raise ValueError("Archived teams cannot be edited.")
        assignment = self.repository.get_division_assignment(team.season_sport_division_id)
        if assignment is None:
            raise LookupError("Season division assignment not found.")
        season = self.repository.get_season_for_assignment(assignment)
        if season is None:
            raise LookupError("Season not found for team.")
        self.policy.validate_registration(
            season_status=season.season_status,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registered_on=date.today(),
        )

        normalized_name = self.policy.normalize_text(name, "Team name", 150)
        if self.repository.name_exists_for_update(
            team.season_sport_division_id,
            normalized_name,
            exclude_id=team_id,
        ):
            raise SeasonTeamConflictError("A team with that name already exists in this division.")
        team.name = normalized_name
        team.barangay = self.policy.normalize_text(barangay, "Barangay", 150)
        team.coach_name = self.policy.normalize_optional_text(coach_name, "Coach name", 150)
        team.manager_name = self.policy.normalize_optional_text(manager_name, "Manager name", 150)
        team.team_color = self.policy.normalize_optional_text(team_color, "Team color", 50)
        self._commit("A team with that name already exists in this division.")
        return team

    def set_archived(self, team_id: int, archived: bool, actor_id: int) -> SeasonTeam:
        team = self.repository.get_team(team_id)
        if team is None:
            raise LookupError("Team not found.")
        if not archived and team.is_archived:
            assignment = self.repository.get_division_assignment(team.season_sport_division_id)
            if assignment is None:
                raise LookupError("Season division assignment not found.")
            season = self.repository.get_season_for_assignment(assignment)
            if season is None:
                raise LookupError("Season not found for team.")
            self.policy.validate_registration(
                season_status=season.season_status,
                registration_start_date=season.registration_start_date,
                registration_end_date=season.registration_end_date,
                registered_on=date.today(),
            )
        team.is_archived = archived
        team.archived_at = datetime.utcnow() if archived else None
        team.archived_by = actor_id if archived else None
        self._commit("Team archive state could not be updated.")
        return team

    def register_team(
        self,
        assignment_id: int,
        *,
        name: str,
        barangay: str,
        coach_name: str | None = None,
        manager_name: str | None = None,
        team_color: str | None = None,
        registered_on: date | None = None,
    ) -> SeasonTeam:
        assignment = self.repository.get_division_assignment(assignment_id)
        if assignment is None:
            raise LookupError("Season division assignment not found.")
        season = self.repository.get_season_for_assignment(assignment)
        if season is None:
            raise LookupError("Season not found for division assignment.")

        registration_date = registered_on or date.today()
        self.policy.validate_registration(
            season_status=season.season_status,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registered_on=registration_date,
        )

        normalized_name = self.policy.normalize_text(name, "Team name", 150)
        normalized_barangay = self.policy.normalize_text(barangay, "Barangay", 150)
        normalized_coach = self.policy.normalize_optional_text(coach_name, "Coach name", 150)
        normalized_manager = self.policy.normalize_optional_text(manager_name, "Manager name", 150)
        normalized_color = self.policy.normalize_optional_text(team_color, "Team color", 50)

        if self.repository.name_exists(assignment_id, normalized_name):
            raise SeasonTeamConflictError("A team with that name already exists in this division.")

        team = SeasonTeam(
            season_sport_division_id=assignment_id,
            name=normalized_name,
            barangay=normalized_barangay,
            coach_name=normalized_coach,
            manager_name=normalized_manager,
            team_color=normalized_color,
        )
        self.repository.add(team)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise SeasonTeamConflictError(
                "A team with that name already exists in this division."
            ) from exc
        return team

    @staticmethod
    def _commit(conflict_message: str) -> None:
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise SeasonTeamConflictError(conflict_message) from exc
