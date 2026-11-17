from sqlalchemy import func

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.statistics import SportStatisticConfiguration, StatisticType
from app.extensions import db


class CatalogRepository(BaseRepository):
    def get_season(self, season_id: int) -> Season | None:
        return db.session.get(Season, season_id)

    def get_season_sport(self, season_sport_id: int) -> SeasonSport | None:
        return db.session.get(SeasonSport, season_sport_id)

    def get_division(self, division_id: int) -> SeasonSportDivision | None:
        return db.session.get(SeasonSportDivision, division_id)

    def season_sports(self, season_id: int) -> list[SeasonSport]:
        return SeasonSport.query.filter_by(season_id=season_id).order_by(SeasonSport.id).all()

    def season_sport_divisions(self, season_sport_id: int) -> list[SeasonSportDivision]:
        return SeasonSportDivision.query.filter_by(season_sport_id=season_sport_id).order_by(SeasonSportDivision.id).all()

    def sport_name_exists(self, season_id: int, name: str, exclude_id: int | None = None) -> bool:
        query = SeasonSport.query.filter(SeasonSport.season_id == season_id, func.lower(SeasonSport.name) == name.lower())
        if exclude_id is not None:
            query = query.filter(SeasonSport.id != exclude_id)
        return query.first() is not None

    def division_name_exists(self, sport_id: int, name: str, exclude_id: int | None = None) -> bool:
        query = SeasonSportDivision.query.filter(
            SeasonSportDivision.season_sport_id == sport_id, func.lower(SeasonSportDivision.name) == name.lower(),
        )
        if exclude_id is not None:
            query = query.filter(SeasonSportDivision.id != exclude_id)
        return query.first() is not None

    def division_assignment_has_teams(self, division_id: int) -> bool:
        return SeasonTeam.query.filter_by(season_sport_division_id=division_id).first() is not None

    def remove_sport_statistics(self, sport_id: int) -> None:
        StatisticType.query.filter_by(season_sport_id=sport_id).delete(synchronize_session=False)
        SportStatisticConfiguration.query.filter_by(season_sport_id=sport_id).delete(synchronize_session=False)

    def add(self, entity) -> None:
        db.session.add(entity)

    def delete(self, entity) -> None:
        db.session.delete(entity)
