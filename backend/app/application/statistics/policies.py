from decimal import Decimal, InvalidOperation

from app.application.games.types import GameSnapshot
from app.application.statistics.types import GameStatistics, StatisticDefinitionInput, TeamStatisticsInput


class StatisticsPolicy:
    def validate_configuration(
        self, definitions: list[StatisticDefinitionInput], allow_team_points: bool,
    ) -> list[StatisticDefinitionInput]:
        if not definitions or not any(item["required"] for item in definitions):
            raise ValueError("Configure at least one required statistic.")
        normalized: list[StatisticDefinitionInput] = []
        names: set[str] = set()
        abbreviations: set[str] = set()
        for item in definitions:
            name, abbreviation = item["name"].strip(), item["abbreviation"].strip()
            if not name or len(name) > 100 or not abbreviation or len(abbreviation) > 20:
                raise ValueError("Each statistic needs a name and abbreviation.")
            if name.casefold() in names or abbreviation.casefold() in abbreviations:
                raise ValueError("Statistic names and abbreviations must be unique within the sport.")
            if item["is_scoring"] and not item["required"]:
                raise ValueError("The scoring statistic must be required.")
            names.add(name.casefold())
            abbreviations.add(abbreviation.casefold())
            normalized.append(StatisticDefinitionInput(
                name=name, abbreviation=abbreviation, required=item["required"], is_scoring=item["is_scoring"],
            ))
        scoring = sum(item["is_scoring"] for item in normalized)
        if scoring > 1:
            raise ValueError("Choose at most one scoring statistic.")
        if allow_team_points and not scoring:
            raise ValueError("Team points require a scoring statistic.")
        return normalized

    def validate_draft(self, expected: GameStatistics, teams: list[TeamStatisticsInput]) -> None:
        config = expected["configuration"]
        if not config["types"]:
            raise ValueError("Configure sport statistics before recording game statistics.")
        expected_teams = {team["team_id"]: team for team in expected["teams"]}
        if len(teams) != len(expected_teams) or {team["team_id"] for team in teams} != set(expected_teams):
            raise ValueError("Submit statistics for both game teams.")
        definitions = {str(item["id"]): item for item in config["types"]}
        any_data = False
        for team in teams:
            if team["team_points"] is not None:
                if not config["allow_team_points"] or not 0 <= team["team_points"] <= 2147483647:
                    raise ValueError("Team points are not enabled or are outside the supported range.")
                any_data = True
            expected_players = {player["player_id"] for player in expected_teams[team["team_id"]]["players"]}
            players = team["players"]
            if len(players) != len(expected_players) or {player["player_id"] for player in players} != expected_players:
                raise ValueError("Submit each rostered player exactly once for their own team.")
            for player in players:
                status, values = player["status"], player["values"]
                if status not in (None, "PLAYED", "DNP"):
                    raise ValueError("Player status must be Played or DNP.")
                if status is not None:
                    any_data = True
                if status != "PLAYED" and values:
                    raise ValueError("Only players marked Played can have statistics.")
                if set(values) - definitions.keys():
                    raise ValueError("A statistic is not configured for this sport.")
                for key, raw in values.items():
                    try:
                        value = Decimal(raw)
                        valid = (
                            value.is_finite()
                            and value.copy_abs() <= Decimal("99999999.99")
                            and value == value.quantize(Decimal("0.01"))
                        )
                    except (InvalidOperation, ValueError):
                        raise ValueError("Statistic values must be valid decimals.") from None
                    if not valid:
                        raise ValueError("Statistic values must have at most two decimals and fit the supported range.")
                    if definitions[key]["is_scoring"] and value < 0:
                        raise ValueError("The scoring statistic cannot be negative.")
        if not any_data:
            raise ValueError("Enter at least one player status or team points before saving.")

    def validate_finalization(self, game: GameSnapshot, data: GameStatistics) -> None:
        config = data["configuration"]
        if not config["types"]:
            raise ValueError("Configure sport statistics before finalizing.")
        required = {str(item["id"]) for item in config["types"] if item["required"]}
        scoring = next((str(item["id"]) for item in config["types"] if item["is_scoring"]), None)
        for team, score in zip(data["teams"], (game.home_score, game.away_score)):
            players = team["players"]
            if not players or any(player["status"] not in ("PLAYED", "DNP") for player in players):
                raise ValueError("Mark every rostered player as Played or DNP before finalizing.")
            if not any(player["status"] == "PLAYED" for player in players):
                raise ValueError("Each team must have at least one player marked Played.")
            for player in players:
                if player["status"] == "PLAYED" and required - player["values"].keys():
                    raise ValueError("Enter every required statistic for each player marked Played.")
            if scoring is not None:
                if config["allow_team_points"] and team["team_points"] is None:
                    raise ValueError("Enter team points for both teams, including zero.")
                total = sum(
                    (Decimal(player["values"][scoring]) for player in players if player["status"] == "PLAYED"),
                    Decimal(0),
                )
                total += team["team_points"] or 0
                if total != score:
                    raise ValueError(f"{team['name']}'s player and team points do not match its game score.")
