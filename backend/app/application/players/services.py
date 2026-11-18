from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.application.common.utils.base_classes import BaseService
from app.application.players.policies import PlayerConflictError as PlayerConflictError, PlayerPolicy
from app.application.players.types import PlayerData, PlayerValues, VoterIdData
from app.infrastructure.database.player_repository import PlayerRepository
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class PlayerService(BaseService):
    def __init__(
        self,
        repository: PlayerRepository | None = None,
        policy: PlayerPolicy | None = None,
        unit_of_work: SqlAlchemyUnitOfWork | None = None,
    ) -> None:
        """Configure the player persistence, business rules, and transaction boundary."""
        self.repository = repository or PlayerRepository()
        self.policy = policy or PlayerPolicy()
        self.unit_of_work = unit_of_work or SqlAlchemyUnitOfWork()

    def list_players(self, *, include_archived: bool = False) -> list[PlayerData]:
        """List profiles, excluding archived players unless requested."""
        return self.repository.list_players(include_archived=include_archived)

    def get_player(self, player_id: int) -> PlayerData:
        """Return a player profile or report that it does not exist."""
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
        voter_year: int | None = None,
        voter_number: str | None = None,
    ) -> PlayerData:
        """Create a normalized profile and reject duplicate identities."""
        values = self._normalize_values(
            first_name, middle_name, last_name, birthdate, gender, address
        )
        voter = self._normalize_voter_id(voter_year, voter_number)
        try:
            with self.unit_of_work:
                self.policy.validate_identity_available(self.repository.identity_exists(
                    values["first_name"], values["middle_name"], values["last_name"],
                    values["birthdate"],
                ))
                player = self.repository.create(values)
                if voter:
                    self.repository.save_voter_id(player["id"], *voter)
        except IntegrityError as exc:
            raise PlayerConflictError(
                "A player identity or voter ID for this year already exists."
            ) from exc
        return player

    def list_voter_ids(self, player_id: int) -> list[VoterIdData]:
        """Return the player's voter IDs for each recorded season year."""
        self.get_player(player_id)
        return self.repository.list_voter_ids(player_id)

    def save_voter_id(self, player_id: int, year: int, voter_number: str) -> None:
        """Save a voter ID and clear verification for seasons in that year."""
        voter = self._normalize_voter_id(year, voter_number)
        if voter is None:
            raise ValueError("A voter ID and season year are required.")
        try:
            with self.unit_of_work:
                self.repository.lock_player(player_id)
                self.policy.validate_editable(self.get_player(player_id)["is_archived"])
                self.repository.save_voter_id(player_id, *voter)
        except IntegrityError as exc:
            raise PlayerConflictError("This voter ID is already assigned in that year.") from exc

    def _normalize_voter_id(self, year: int | None, number: str | None) -> tuple[int, str] | None:
        """Validate a voter ID and its associated season year."""
        if year is None and not number:
            return None
        if year is None or year < 1:
            raise ValueError("A valid season year is required for the voter ID.")
        normalized = self.policy.normalize_required(number or "", "Voter ID", 100)
        if len(normalized.casefold()) > 200:
            raise ValueError("Voter ID is too long after normalization.")
        return year, normalized

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
    ) -> PlayerData:
        """Update an active profile while preserving identity uniqueness."""
        try:
            with self.unit_of_work:
                player = self.get_player(player_id)
                self.policy.validate_editable(player["is_archived"])
                values = self._normalize_values(
                    first_name, middle_name, last_name, birthdate, gender, address
                )
                self.policy.validate_identity_available(self.repository.identity_exists(
                    values["first_name"], values["middle_name"], values["last_name"],
                    values["birthdate"], exclude_id=player_id,
                ))
                updated = self.repository.update(player_id, values)
        except IntegrityError as exc:
            raise PlayerConflictError(
                "A player with this name and birthdate already exists."
            ) from exc
        return updated

    def set_archived(self, player_id: int, archived: bool, actor_id: int) -> PlayerData:
        """Archive or restore a profile, retaining existing metadata on a no-op."""
        player = self.get_player(player_id)
        if player["is_archived"] == archived:
            return player
        try:
            with self.unit_of_work:
                player = self.repository.set_archived(
                    player_id, archived, actor_id,
                    datetime.now(timezone.utc).replace(tzinfo=None),
                )
        except IntegrityError as exc:
            raise PlayerConflictError("Player archive state could not be updated.") from exc
        return player

    def _normalize_values(
        self,
        first_name: str,
        middle_name: str | None,
        last_name: str,
        birthdate: date,
        gender: str,
        address: str,
    ) -> PlayerValues:
        """Apply field normalization and birthdate validation before persistence."""
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
