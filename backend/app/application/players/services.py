from datetime import date, datetime

from sqlalchemy.exc import IntegrityError

from app.application.common.utils.base_classes import BaseService
from app.application.players.policies import PlayerPolicy
from app.domain.models.players import Player
from app.extensions import db
from app.infrastructure.database.player_repository import PlayerRepository


class PlayerConflictError(ValueError):
    pass


class PlayerService(BaseService):
    def __init__(
        self,
        repository: PlayerRepository | None = None,
        policy: PlayerPolicy | None = None,
    ) -> None:
        self.repository = repository or PlayerRepository()
        self.policy = policy or PlayerPolicy()

    def list_players(self, *, include_archived: bool = False) -> list[Player]:
        return self.repository.list_players(include_archived=include_archived)

    def get_player(self, player_id: int) -> Player:
        player = self.repository.get(player_id)
        if player is None:
            raise LookupError("Player not found.")
        return player

    def create_player(
        self,
        *,
        first_name: str,
        middle_name: str | None,
        last_name: str,
        birthdate: date,
        gender: str,
        address: str,
    ) -> Player:
        values = self._normalize_values(
            first_name, middle_name, last_name, birthdate, gender, address
        )
        if self.repository.identity_exists(
            values["first_name"],
            values["middle_name"],
            values["last_name"],
            values["birthdate"],
        ):
            raise PlayerConflictError("A player with this name and birthdate already exists.")

        player = Player(**values)
        self.repository.add(player)
        self._commit("A player with this name and birthdate already exists.")
        return player

    def update_player(
        self,
        player_id: int,
        *,
        first_name: str,
        middle_name: str | None,
        last_name: str,
        birthdate: date,
        gender: str,
        address: str,
    ) -> Player:
        player = self.get_player(player_id)
        if player.is_archived:
            raise ValueError("Archived player profiles cannot be edited; restore the profile first.")
        values = self._normalize_values(
            first_name, middle_name, last_name, birthdate, gender, address
        )
        if self.repository.identity_exists(
            values["first_name"],
            values["middle_name"],
            values["last_name"],
            values["birthdate"],
            exclude_id=player_id,
        ):
            raise PlayerConflictError("A player with this name and birthdate already exists.")

        for key, value in values.items():
            setattr(player, key, value)
        self._commit("A player with this name and birthdate already exists.")
        return player

    def set_archived(self, player_id: int, archived: bool, actor_id: int) -> Player:
        player = self.get_player(player_id)
        if player.is_archived == archived:
            return player
        player.is_archived = archived
        player.archived_at = datetime.utcnow() if archived else None
        player.archived_by = actor_id if archived else None
        self._commit("Player archive state could not be updated.")
        return player

    def _normalize_values(
        self,
        first_name: str,
        middle_name: str | None,
        last_name: str,
        birthdate: date,
        gender: str,
        address: str,
    ) -> dict:
        first = self.policy.normalize_required(first_name, "First name", 100)
        middle = self.policy.normalize_optional(middle_name, 100)
        last = self.policy.normalize_required(last_name, "Last name", 100)
        normalized_gender = self.policy.normalize_required(gender, "Gender", 20)
        normalized_address = self.policy.normalize_required(address, "Address", 1000)
        self.policy.validate_birthdate(birthdate)
        return {
            "first_name": first,
            "middle_name": middle,
            "last_name": last,
            "birthdate": birthdate,
            "gender": normalized_gender,
            "address": normalized_address,
        }

    @staticmethod
    def _commit(conflict_message: str) -> None:
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise PlayerConflictError(conflict_message) from exc
