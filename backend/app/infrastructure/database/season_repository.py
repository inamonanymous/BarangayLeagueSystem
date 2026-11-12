from sqlalchemy import and_, func

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.divisions import Division
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.seasons import Season
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.extensions import db


class SeasonRepository(BaseRepository):
    def list_all(self) -> list[Season]:
        return Season.query.order_by(Season.year.desc(), Season.id.desc()).all()

    def get_by_id(self, season_id: int) -> Season | None:
        return db.session.get(Season, season_id)

    def exists_by_name(self, name: str) -> bool:
        return Season.query.filter_by(name=name).first() is not None

    def has_active_season(self, *, exclude_id: int | None = None) -> bool:
        query = Season.query.filter(
            Season.season_status.in_(("REGISTRATION", "ONGOING"))
        )
        if exclude_id is not None:
            query = query.filter(Season.id != exclude_id)
        return query.first() is not None

    def list_teams_below_minimum_roster_size(self, season_id: int) -> list[dict]:
        active_player_count = func.count(Player.id)
        rows = (
            db.session.query(
                SeasonTeam.name.label("team_name"),
                Division.name.label("division_name"),
                active_player_count.label("roster_count"),
                Division.minimum_roster_size.label("minimum_roster_size"),
            )
            .join(
                SeasonSportDivision,
                SeasonTeam.season_sport_division_id == SeasonSportDivision.id,
            )
            .join(SeasonSport, SeasonSportDivision.season_sport_id == SeasonSport.id)
            .join(Division, SeasonSportDivision.division_id == Division.id)
            .outerjoin(Roster, Roster.season_team_id == SeasonTeam.id)
            .outerjoin(
                Player,
                and_(Player.id == Roster.player_id, Player.is_archived.is_(False)),
            )
            .filter(
                SeasonSport.season_id == season_id,
                SeasonTeam.is_archived.is_(False),
            )
            .group_by(
                SeasonTeam.id,
                SeasonTeam.name,
                Division.id,
                Division.name,
                Division.minimum_roster_size,
            )
            .having(active_player_count < Division.minimum_roster_size)
            .order_by(Division.name.asc(), SeasonTeam.name.asc())
            .all()
        )
        return [
            {
                "team_name": row.team_name,
                "division_name": row.division_name,
                "roster_count": row.roster_count,
                "minimum_roster_size": row.minimum_roster_size,
            }
            for row in rows
        ]

    def add(self, season: Season) -> None:
        db.session.add(season)