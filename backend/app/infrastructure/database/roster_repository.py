from datetime import datetime

from sqlalchemy import func

from app.application.common.utils.base_classes import BaseRepository
from app.application.rosters.types import (
    DivisionSnapshot,
    PlayerData,
    PlayerSnapshot,
    RosterData,
    RosterEntryData,
    RosterSnapshot,
    SeasonSnapshot,
    TeamSnapshot,
)
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.seasons import Season
from app.extensions import db
from app.infrastructure.database.team_roster_lock import lock_team_roster


class RosterRepository(BaseRepository):
    def lock_team_roster(self, team_id: int) -> None:
        lock_team_roster(team_id)

    def get_team(self, team_id: int, *, for_update: bool = False) -> TeamSnapshot | None:
        query = SeasonTeam.query.filter_by(id=team_id)
        if for_update:
            query = query.populate_existing().with_for_update()
        team = query.first()
        if team is None:
            return None
        return TeamSnapshot(team.id, team.season_sport_division_id, team.is_archived)

    def get_player(self, player_id: int) -> PlayerSnapshot | None:
        player = db.session.get(Player, player_id)
        if player is None:
            return None
        return PlayerSnapshot(player.birthdate, player.is_archived)

    def get_roster(self, roster_id: int) -> RosterSnapshot | None:
        roster = db.session.get(Roster, roster_id)
        if roster is None:
            return None
        return RosterSnapshot(roster.id, roster.season_team_id)

    def get_season_details(
        self, team: TeamSnapshot,
    ) -> tuple[SeasonSnapshot | None, DivisionSnapshot | None, int | None]:
        assignment = db.session.get(SeasonSportDivision, team.season_sport_division_id)
        if assignment is None:
            return None, None, None
        season_sport = db.session.get(SeasonSport, assignment.season_sport_id)
        division_snapshot = DivisionSnapshot(assignment.maximum_roster_size)
        if season_sport is None:
            return None, division_snapshot, None
        season = db.session.get(Season, season_sport.season_id)
        season_snapshot = (
            SeasonSnapshot(
                season.id, season.season_status,
                season.registration_start_date, season.registration_end_date,
            ) if season is not None else None
        )
        return season_snapshot, division_snapshot, season_sport.id

    def list_for_team(self, team_id: int) -> list[RosterEntryData]:
        rows = (
            db.session.query(Roster, Player)
            .join(Player, Player.id == Roster.player_id)
            .filter(Roster.season_team_id == team_id)
            .order_by(Roster.jersey_number.asc())
            .all()
        )
        return [
            RosterEntryData(**self._roster_data(roster), player=self._player_data(player))
            for roster, player in rows
        ]

    def player_already_on_team(self, team_id: int, player_id: int) -> bool:
        return Roster.query.filter_by(season_team_id=team_id, player_id=player_id).first() is not None

    def player_on_same_sport_in_season(
        self,
        player_id: int,
        season_id: int,
        sport_id: int,
    ) -> bool:
        return (
            self._players_on_same_sport_in_season(season_id, sport_id)
            .filter(Roster.player_id == player_id)
            .with_for_update()
            .first()
            is not None
        )

    def list_available_players(self, season_id: int, sport_id: int) -> list[PlayerData]:
        assigned_players = self._players_on_same_sport_in_season(season_id, sport_id)
        players = (
            Player.query
            .filter(Player.is_archived.is_(False), ~Player.id.in_(assigned_players))
            .order_by(Player.last_name, Player.first_name, Player.id)
            .all()
        )
        return [self._player_data(player) for player in players]

    def _players_on_same_sport_in_season(self, season_id: int, sport_id: int):
        return (
            db.session.query(Roster.player_id)
            .join(SeasonTeam, Roster.season_team_id == SeasonTeam.id)
            .join(SeasonSportDivision, SeasonTeam.season_sport_division_id == SeasonSportDivision.id)
            .join(SeasonSport, SeasonSportDivision.season_sport_id == SeasonSport.id)
            .filter(
                SeasonTeam.is_archived.is_(False),
                SeasonSport.season_id == season_id,
                SeasonSport.id == sport_id,
            )
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

    def save_eligibility(
        self, season_id: int, player_id: int, voter_number: str,
        actor_id: int, notes: str | None,
    ) -> None:
        eligibility = SeasonPlayerEligibility.query.filter_by(
            season_id=season_id, player_id=player_id,
        ).first()
        normalized_notes = (notes or "").strip()
        if eligibility is None:
            eligibility = SeasonPlayerEligibility(
                season_id=season_id, player_id=player_id, is_voter_verified=True,
                voter_number=voter_number, verified_by=actor_id,
                verified_at=datetime.utcnow(), notes=normalized_notes or None,
            )
            db.session.add(eligibility)
        else:
            eligibility.is_voter_verified = True
            eligibility.voter_number = voter_number
            eligibility.verified_by = actor_id
            eligibility.verified_at = datetime.utcnow()
            eligibility.notes = normalized_notes or eligibility.notes

    def add_roster(self, team_id: int, player_id: int, jersey_number: str) -> RosterData:
        roster = Roster(season_team_id=team_id, player_id=player_id, jersey_number=jersey_number)
        db.session.add(roster)
        db.session.flush()
        return self._roster_data(roster)

    def update_jersey(self, roster_id: int, jersey_number: str) -> RosterData:
        roster = db.session.get(Roster, roster_id)
        if roster is None:
            raise LookupError("Roster entry not found for this team.")
        roster.jersey_number = jersey_number
        db.session.flush()
        return self._roster_data(roster)

    def delete_roster(self, roster_id: int) -> None:
        roster = db.session.get(Roster, roster_id)
        if roster is None:
            raise LookupError("Roster entry not found for this team.")
        db.session.delete(roster)

    @staticmethod
    def _roster_data(roster: Roster) -> RosterData:
        return RosterData(**roster.to_dict())

    @staticmethod
    def _player_data(player: Player) -> PlayerData:
        return PlayerData(**player.to_dict())
