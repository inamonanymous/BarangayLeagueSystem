from sqlalchemy import func

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.extensions import db


class PlayerRepository(BaseRepository):
    def list_players(self, *, include_archived: bool = False) -> list[Player]:
        query = Player.query
        if not include_archived:
            query = query.filter_by(is_archived=False)
        return query.order_by(Player.last_name.asc(), Player.first_name.asc(), Player.id.asc()).all()

    def get(self, player_id: int) -> Player | None:
        return db.session.get(Player, player_id)

    def identity_exists(
        self,
        first_name: str,
        middle_name: str,
        last_name: str,
        birthdate,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        query = Player.query.filter(
            func.lower(Player.first_name) == first_name.casefold(),
            func.lower(Player.middle_name) == middle_name.casefold(),
            func.lower(Player.last_name) == last_name.casefold(),
            Player.birthdate == birthdate,
        )
        if exclude_id is not None:
            query = query.filter(Player.id != exclude_id)
        return query.first() is not None

    def has_rosters(self, player_id: int) -> bool:
        return Roster.query.filter_by(player_id=player_id).first() is not None

    def add(self, player: Player) -> None:
        db.session.add(player)
