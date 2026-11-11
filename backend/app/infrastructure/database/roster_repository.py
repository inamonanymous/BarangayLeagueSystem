from sqlalchemy import func

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.divisions import Division
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.seasons import Season
from app.extensions import db


class RosterRepository(BaseRepository):
    def get_team(self, team_id: int) -> SeasonTeam | None:
        return db.session.get(SeasonTeam, team_id)

    def get_player(self, player_id: int) -> Player | None:
        return db.session.get(Player, player_id)

    def get_roster(self, roster_id: int) -> Roster | None:
        return db.session.get(Roster, roster_id)

    def get_season_details(self, team: SeasonTeam) -> tuple[Season | None, Division | None, int | None]:
        assignment = db.session.get(SeasonSportDivision, team.season_sport_division_id)
        if assignment is None:
            return None, None, None
        season_sport = db.session.get(SeasonSport, assignment.season_sport_id)
        division = db.session.get(Division, assignment.division_id)
        if season_sport is None:
            return None, division, None
        return db.session.get(Season, season_sport.season_id), division, season_sport.sport_id

    def list_for_team(self, team_id: int) -> list[Roster]:
        return Roster.query.filter_by(season_team_id=team_id).order_by(Roster.jersey_number.asc()).all()

    def list_active_players(self) -> list[Player]:
        return Player.query.filter_by(is_archived=False).order_by(Player.last_name, Player.first_name).all()

    def player_already_on_team(self, team_id: int, player_id: int) -> bool:
        return Roster.query.filter_by(season_team_id=team_id, player_id=player_id).first() is not None

    def player_on_same_sport_in_season(
        self,
        player_id: int,
        season_id: int,
        sport_id: int,
    ) -> bool:
        return (
            db.session.query(Roster.id)
            .join(SeasonTeam, Roster.season_team_id == SeasonTeam.id)
            .join(SeasonSportDivision, SeasonTeam.season_sport_division_id == SeasonSportDivision.id)
            .join(SeasonSport, SeasonSportDivision.season_sport_id == SeasonSport.id)
            .filter(
                Roster.player_id == player_id,
                SeasonTeam.is_archived.is_(False),
                SeasonSport.season_id == season_id,
                SeasonSport.sport_id == sport_id,
            )
            .first()
            is not None
        )

    def jersey_exists(self, team_id: int, jersey_number: str, *, exclude_id: int | None = None) -> bool:
        query = Roster.query.filter(
            Roster.season_team_id == team_id,
            func.lower(Roster.jersey_number) == jersey_number.casefold(),
        )
        if exclude_id is not None:
            query = query.filter(Roster.id != exclude_id)
        return query.first() is not None

    def roster_count(self, team_id: int) -> int:
        return Roster.query.filter_by(season_team_id=team_id).count()

    def find_eligibility(self, season_id: int, player_id: int) -> SeasonPlayerEligibility | None:
        return SeasonPlayerEligibility.query.filter_by(
            season_id=season_id,
            player_id=player_id,
        ).first()

    def add(self, entity) -> None:
        db.session.add(entity)

    def delete(self, entity) -> None:
        db.session.delete(entity)
