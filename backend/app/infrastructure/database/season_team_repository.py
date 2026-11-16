from sqlalchemy import func
from sqlalchemy.orm import aliased

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.extensions import db
from app.infrastructure.database.team_roster_lock import lock_team_roster


class SeasonTeamRepository(BaseRepository):
    def lock_team_roster(self, team_id: int) -> None:
        lock_team_roster(team_id)

    def get_team(self, team_id: int) -> SeasonTeam | None:
        return db.session.get(SeasonTeam, team_id)

    def get_team_for_update(self, team_id: int) -> SeasonTeam | None:
        return SeasonTeam.query.filter_by(id=team_id).populate_existing().with_for_update().first()

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

    def list_restore_conflicts(
        self, team_id: int, season_sport_id: int,
    ) -> list[tuple[int, str, int, str]]:
        original_roster = aliased(Roster)
        rows = (
            db.session.query(Player, SeasonTeam)
            .join(Roster, Roster.player_id == Player.id)
            .join(original_roster, original_roster.player_id == Player.id)
            .join(SeasonTeam, SeasonTeam.id == Roster.season_team_id)
            .join(SeasonSportDivision, SeasonSportDivision.id == SeasonTeam.season_sport_division_id)
            .filter(
                original_roster.season_team_id == team_id,
                SeasonTeam.id != team_id,
                SeasonTeam.is_archived.is_(False),
                SeasonSportDivision.season_sport_id == season_sport_id,
            )
            .order_by(Player.last_name, Player.first_name, Player.id, SeasonTeam.name, SeasonTeam.id)
            .with_for_update()
            .all()
        )
        return [
            (player.id, " ".join(part for part in (player.first_name, player.middle_name, player.last_name) if part),
             team.id, team.name)
            for player, team in rows
        ]

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
