from datetime import date, datetime

from sqlalchemy import func

from app.application.common.utils.base_classes import BaseRepository
from app.application.players.types import PlayerData, PlayerValues, VoterIdData
from app.domain.models.players import Player
from app.domain.models.player_voter_ids import PlayerVoterId
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.domain.models.seasons import Season
from app.extensions import db


class PlayerRepository(BaseRepository):
    def lock_player(self, player_id: int) -> None:
        if Player.query.filter_by(id=player_id).populate_existing().with_for_update().first() is None:
            raise LookupError("Player not found.")

    def list_voter_ids(self, player_id: int) -> list[VoterIdData]:
        rows = PlayerVoterId.query.filter_by(player_id=player_id).order_by(PlayerVoterId.year.desc()).all()
        return [VoterIdData(year=row.year, voter_number=row.voter_number) for row in rows]

    def save_voter_id(self, player_id: int, year: int, number: str) -> None:
        record = PlayerVoterId.query.filter_by(player_id=player_id, year=year).first()
        if record is None:
            record = PlayerVoterId(player_id=player_id, year=year, voter_number=number, normalized_number=number.casefold())
            db.session.add(record)
        elif record.voter_number == number:
            return
        else:
            record.voter_number = number
            record.normalized_number = number.casefold()
        season_ids = db.session.query(Season.id).filter(Season.year == year)
        SeasonPlayerEligibility.query.filter(
            SeasonPlayerEligibility.player_id == player_id,
            SeasonPlayerEligibility.season_id.in_(season_ids),
        ).update({"is_voter_verified": False, "verified_by": None, "verified_at": None}, synchronize_session=False)
        db.session.flush()

    def list_players(self, *, include_archived: bool = False) -> list[PlayerData]:
        query = Player.query
        if not include_archived:
            query = query.filter_by(is_archived=False)
        players = query.order_by(Player.last_name.asc(), Player.first_name.asc(), Player.id.asc()).all()
        return [self._player_data(player) for player in players]

    def get(self, player_id: int) -> PlayerData | None:
        player = db.session.get(Player, player_id)
        return self._player_data(player) if player is not None else None

    def identity_exists(
        self,
        first_name: str,
        middle_name: str,
        last_name: str,
        birthdate: date,
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

    def create(self, values: PlayerValues) -> PlayerData:
        player = Player(**values)
        db.session.add(player)
        db.session.flush()
        return self._player_data(player)

    def update(self, player_id: int, values: PlayerValues) -> PlayerData:
        player = self._require_player(player_id)
        for key, value in values.items():
            setattr(player, key, value)
        db.session.flush()
        return self._player_data(player)

    def set_archived(
        self, player_id: int, archived: bool, actor_id: int, now: datetime,
    ) -> PlayerData:
        player = self._require_player(player_id)
        player.is_archived = archived
        player.archived_at = now if archived else None
        player.archived_by = actor_id if archived else None
        db.session.flush()
        return self._player_data(player)

    def _require_player(self, player_id: int) -> Player:
        player = db.session.get(Player, player_id)
        if player is None:
            raise LookupError("Player not found.")
        return player

    @staticmethod
    def _player_data(player: Player) -> PlayerData:
        return PlayerData(**player.to_dict())
