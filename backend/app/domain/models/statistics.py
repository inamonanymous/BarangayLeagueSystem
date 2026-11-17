from app.extensions import db


class SportStatisticConfiguration(db.Model):
    __tablename__ = "sport_statistic_configurations"

    season_sport_id = db.Column(db.Integer, db.ForeignKey("season_sports.id", ondelete="CASCADE"), primary_key=True)
    allow_team_points = db.Column(db.Boolean, nullable=False, default=False)
    locked = db.Column(db.Boolean, nullable=False, default=False)


class StatisticType(db.Model):
    __tablename__ = "statistic_types"

    id = db.Column(db.Integer, primary_key=True)
    season_sport_id = db.Column(
        db.Integer, db.ForeignKey("sport_statistic_configurations.season_sport_id", ondelete="CASCADE"), nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(20), nullable=False)
    required = db.Column(db.Boolean, nullable=False)
    is_scoring = db.Column(db.Boolean, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("season_sport_id", "name", name="uq_statistic_type_sport_name"),
        db.UniqueConstraint("season_sport_id", "abbreviation", name="uq_statistic_type_sport_abbreviation"),
    )


class GameParticipant(db.Model):
    __tablename__ = "game_participants"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey("season_teams.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    status = db.Column(db.String(10), nullable=False)

    __table_args__ = (db.UniqueConstraint("game_id", "player_id", name="uq_game_participant_player"),)


class PlayerGameStatistic(db.Model):
    __tablename__ = "player_game_statistics"

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("game_participants.id"), nullable=False)
    statistic_type_id = db.Column(db.Integer, db.ForeignKey("statistic_types.id"), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("participant_id", "statistic_type_id", name="uq_participant_statistic_type"),
    )


class GameTeamPoints(db.Model):
    __tablename__ = "game_team_points"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("season_teams.id"), nullable=False)
    points = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("game_id", "team_id", name="uq_game_team_points"),)
