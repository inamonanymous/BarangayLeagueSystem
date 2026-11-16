from sqlalchemy import select, update

from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.extensions import db


def lock_team_roster(team_id: int) -> None:
    season_sport_id = (
        select(SeasonSportDivision.season_sport_id)
        .join(SeasonTeam, SeasonTeam.season_sport_division_id == SeasonSportDivision.id)
        .where(SeasonTeam.id == team_id)
        .scalar_subquery()
    )
    # Serialize roster additions and archive/restore across the same season and sport.
    db.session.execute(
        update(SeasonSport)
        .where(SeasonSport.id == season_sport_id)
        .values(id=SeasonSport.id, updated_at=SeasonSport.updated_at)
    )
