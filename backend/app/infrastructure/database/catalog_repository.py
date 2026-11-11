from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.divisions import Division
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.sports import Sport
from app.extensions import db


class CatalogRepository(BaseRepository):
    def list_sports(self) -> list[Sport]:
        return Sport.query.order_by(Sport.name.asc()).all()

    def list_divisions(self) -> list[Division]:
        return Division.query.order_by(Division.name.asc()).all()

    def get_sport(self, sport_id: int) -> Sport | None:
        return db.session.get(Sport, sport_id)

    def sport_is_assigned(self, sport_id: int) -> bool:
        return SeasonSport.query.filter_by(sport_id=sport_id).first() is not None

    def sport_assignments(self, season_id: int) -> list[SeasonSport]:
        return SeasonSport.query.filter_by(season_id=season_id).all()

    def get_division(self, division_id: int) -> Division | None:
        return db.session.get(Division, division_id)

    def division_is_assigned(self, division_id: int) -> bool:
        return SeasonSportDivision.query.filter_by(division_id=division_id).first() is not None

    def delete(self, entity) -> None:
        db.session.delete(entity)

    def get_season(self, season_id: int) -> Season | None:
        return db.session.get(Season, season_id)

    def get_season_sport(self, season_sport_id: int) -> SeasonSport | None:
        return db.session.get(SeasonSport, season_sport_id)

    def find_season_sport(self, season_id: int, sport_id: int) -> SeasonSport | None:
        return SeasonSport.query.filter_by(season_id=season_id, sport_id=sport_id).first()

    def season_sports(self, season_id: int) -> list[SeasonSport]:
        return SeasonSport.query.filter_by(season_id=season_id).order_by(SeasonSport.id.asc()).all()

    def season_sport_divisions(self, season_sport_id: int) -> list[SeasonSportDivision]:
        return (
            SeasonSportDivision.query
            .filter_by(season_sport_id=season_sport_id)
            .order_by(SeasonSportDivision.id.asc())
            .all()
        )

    def division_for_season_sport(self, season_sport_id: int, division_id: int) -> SeasonSportDivision | None:
        return SeasonSportDivision.query.filter_by(
            season_sport_id=season_sport_id,
            division_id=division_id,
        ).first()

    def add(self, entity) -> None:
        db.session.add(entity)