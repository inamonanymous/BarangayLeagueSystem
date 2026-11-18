from sqlalchemy import and_, func
from datetime import date

from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.players import Player
from app.domain.models.player_voter_ids import PlayerVoterId
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.domain.models.seasons import Season
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.extensions import db
from app.application.rosters.policies import RosterPolicy


class SeasonRepository(BaseRepository):
    def list_all(self) -> list[Season]:
        return Season.query.order_by(Season.year.desc(), Season.id.desc()).all()

    def get_by_id(self, season_id: int) -> Season | None:
        return db.session.get(Season, season_id)

    def get_for_update(self, season_id: int) -> Season | None:
        return Season.query.filter_by(id=season_id).populate_existing().with_for_update().first()

    def exists_by_name(self, name: str) -> bool:
        return Season.query.filter_by(name=name).first() is not None

    def has_active_season(self, *, exclude_id: int | None = None) -> bool:
        query = Season.query.filter(
            Season.season_status.in_(("REGISTRATION", "ONGOING"))
        )
        if exclude_id is not None:
            query = query.filter(Season.id != exclude_id)
        return query.first() is not None

    def count_unverified_adults(self, season_id: int, year: int, today: date) -> int:
        rows = (
            db.session.query(Player, PlayerVoterId, SeasonPlayerEligibility)
            .join(Roster, Roster.player_id == Player.id)
            .join(SeasonTeam, SeasonTeam.id == Roster.season_team_id)
            .join(SeasonSportDivision, SeasonSportDivision.id == SeasonTeam.season_sport_division_id)
            .join(SeasonSport, SeasonSport.id == SeasonSportDivision.season_sport_id)
            .outerjoin(PlayerVoterId, and_(PlayerVoterId.player_id == Player.id, PlayerVoterId.year == year))
            .outerjoin(SeasonPlayerEligibility, and_(
                SeasonPlayerEligibility.player_id == Player.id, SeasonPlayerEligibility.season_id == season_id,
            ))
            .filter(SeasonSport.season_id == season_id, SeasonTeam.is_archived.is_(False), Player.is_archived.is_(False))
            .all()
        )
        return len({
            player.id for player, voter, eligibility in rows
            if RosterPolicy.is_adult(player.birthdate, today)
            and (voter is None or eligibility is None or not eligibility.is_voter_verified
                 or eligibility.voter_number != voter.voter_number)
        })

    def list_teams_below_minimum_roster_size(self, season_id: int) -> list[dict]:
        active_player_count = func.count(Player.id)
        rows = (
            db.session.query(
                SeasonTeam.name.label("team_name"),
                SeasonSportDivision.name.label("division_name"),
                active_player_count.label("roster_count"),
                SeasonSportDivision.minimum_roster_size.label("minimum_roster_size"),
            )
            .join(
                SeasonSportDivision,
                SeasonTeam.season_sport_division_id == SeasonSportDivision.id,
            )
            .join(SeasonSport, SeasonSportDivision.season_sport_id == SeasonSport.id)
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
                SeasonSportDivision.id,
                SeasonSportDivision.name,
                SeasonSportDivision.minimum_roster_size,
            )
            .having(active_player_count < SeasonSportDivision.minimum_roster_size)
            .order_by(SeasonSportDivision.name.asc(), SeasonTeam.name.asc())
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