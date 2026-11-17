from decimal import Decimal

from app.application.games.types import GameSnapshot
from app.application.statistics.types import (
    GameStatistics, ParticipantStatistics, StatisticConfiguration, StatisticDefinition,
    StatisticDefinitionInput, TeamStatistics, TeamStatisticsInput,
)
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.statistics import (
    GameParticipant, GameTeamPoints, PlayerGameStatistic, SportStatisticConfiguration, StatisticType,
)
from app.extensions import db


class StatisticsRepository:
    def sport_exists(self, sport_id: int) -> bool:
        return db.session.get(SeasonSport, sport_id) is not None

    def configuration(self, sport_id: int) -> StatisticConfiguration:
        config = db.session.get(SportStatisticConfiguration, sport_id)
        definitions = StatisticType.query.filter_by(season_sport_id=sport_id).order_by(StatisticType.id).all()
        return StatisticConfiguration(
            season_sport_id=sport_id,
            locked=config.locked if config else False,
            allow_team_points=config.allow_team_points if config else False,
            types=[
                StatisticDefinition(
                    id=item.id, name=item.name, abbreviation=item.abbreviation,
                    required=item.required, is_scoring=item.is_scoring,
                )
                for item in definitions
            ],
        )

    def replace_configuration(
        self, sport_id: int, definitions: list[StatisticDefinitionInput], allow_team_points: bool,
    ) -> StatisticConfiguration:
        config = db.session.get(SportStatisticConfiguration, sport_id)
        if config is None:
            config = SportStatisticConfiguration(season_sport_id=sport_id, locked=False)
            db.session.add(config)
            db.session.flush()
        config.allow_team_points = allow_team_points
        StatisticType.query.filter_by(season_sport_id=sport_id).delete(synchronize_session=False)
        for item in definitions:
            db.session.add(StatisticType(season_sport_id=sport_id, **item))
        db.session.flush()
        return self.configuration(sport_id)

    def game_statistics(self, game: GameSnapshot, sport_id: int) -> GameStatistics:
        configuration = self.configuration(sport_id)
        participants = GameParticipant.query.filter_by(game_id=game.id).all()
        participants_by_player = {participant.player_id: participant for participant in participants}
        values = (
            db.session.query(PlayerGameStatistic)
            .join(GameParticipant, GameParticipant.id == PlayerGameStatistic.participant_id)
            .filter(GameParticipant.game_id == game.id).all()
        )
        values_by_participant: dict[int, dict[str, str]] = {}
        for value in values:
            values_by_participant.setdefault(value.participant_id, {})[str(value.statistic_type_id)] = str(value.value)
        team_points = {item.team_id: item.points for item in GameTeamPoints.query.filter_by(game_id=game.id).all()}
        teams: list[TeamStatistics] = []
        seen: set[int] = set()
        for team_id in (game.home_team_id, game.away_team_id):
            team = db.session.get(SeasonTeam, team_id)
            if team is None:
                raise ValueError("A game team no longer exists.")
            roster = (
                db.session.query(Roster, Player).join(Player, Player.id == Roster.player_id)
                .filter(Roster.season_team_id == team_id).order_by(Roster.id).all()
            )
            players: list[ParticipantStatistics] = []
            for entry, player in roster:
                participant = participants_by_player.get(player.id)
                if participant is not None and participant.team_id != team_id:
                    raise ValueError("A recorded participant no longer belongs to the game team.")
                seen.add(player.id)
                players.append(ParticipantStatistics(
                    player_id=player.id,
                    name=" ".join(part for part in (player.first_name, player.middle_name, player.last_name) if part),
                    jersey_number=entry.jersey_number,
                    status=participant.status if participant else None,
                    values=values_by_participant.get(participant.id, {}) if participant else {},
                ))
            teams.append(TeamStatistics(
                team_id=team_id, name=team.name, team_points=team_points.get(team_id), players=players,
            ))
        if set(participants_by_player) - seen:
            raise ValueError("A recorded participant no longer belongs to a game roster.")
        return GameStatistics(configuration=configuration, teams=teams)

    def replace_game_statistics(self, game_id: int, sport_id: int, teams: list[TeamStatisticsInput]) -> None:
        participant_ids = db.session.query(GameParticipant.id).filter_by(game_id=game_id)
        PlayerGameStatistic.query.filter(PlayerGameStatistic.participant_id.in_(participant_ids)).delete(
            synchronize_session=False,
        )
        GameParticipant.query.filter_by(game_id=game_id).delete(synchronize_session=False)
        GameTeamPoints.query.filter_by(game_id=game_id).delete(synchronize_session=False)
        db.session.flush()
        for team in teams:
            if team["team_points"] is not None:
                db.session.add(GameTeamPoints(game_id=game_id, team_id=team["team_id"], points=team["team_points"]))
            for player in team["players"]:
                if player["status"] is None:
                    continue
                participant = GameParticipant(
                    game_id=game_id, team_id=team["team_id"], player_id=player["player_id"], status=player["status"],
                )
                db.session.add(participant)
                db.session.flush()
                for statistic_id, value in player["values"].items():
                    db.session.add(PlayerGameStatistic(
                        participant_id=participant.id, statistic_type_id=int(statistic_id), value=Decimal(value),
                    ))
        config = db.session.get(SportStatisticConfiguration, sport_id)
        if config is None:
            raise ValueError("Configure sport statistics before recording game statistics.")
        config.locked = True
        db.session.flush()
