from sqlalchemy import func

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.extensions import db


class SeasonTeamRepository(BaseRepository):
    def get_team(self, team_id: int) -> SeasonTeam | None:
        return db.session.get(SeasonTeam, team_id)

    def get_division_assignment(self, assignment_id: int) -> SeasonSportDivision | None:
        return db.session.get(SeasonSportDivision, assignment_id)

    def get_season_for_assignment(self, assignment: SeasonSportDivision) -> Season | None:
        season_sport = db.session.get(SeasonSport, assignment.season_sport_id)
        if season_sport is None:
            return None
        return db.session.get(Season, season_sport.season_id)

    def list_for_division(self, assignment_id: int) -> list[SeasonTeam]:
        return (
            SeasonTeam.query
            .filter_by(season_sport_division_id=assignment_id)
            .order_by(SeasonTeam.name.asc(), SeasonTeam.id.asc())
            .all()
        )

    def name_exists(self, assignment_id: int, name: str) -> bool:
        return (
            SeasonTeam.query
            .filter(
                SeasonTeam.season_sport_division_id == assignment_id,
                func.lower(SeasonTeam.name) == name.casefold(),
            )
            .first()
            is not None
        )

    def name_exists_for_update(self, assignment_id: int, name: str, exclude_id: int) -> bool:
        return (
            SeasonTeam.query
            .filter(
                SeasonTeam.season_sport_division_id == assignment_id,
                func.lower(SeasonTeam.name) == name.casefold(),
                SeasonTeam.id != exclude_id,
            )
            .first()
            is not None
        )

    def add(self, team: SeasonTeam) -> None:
        db.session.add(team)
