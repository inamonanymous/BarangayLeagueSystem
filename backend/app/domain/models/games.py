from app.extensions import db


class ScheduleLock(db.Model):
    __tablename__ = "schedule_lock"

    id = db.Column(db.Integer, primary_key=True)


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    season_sport_division_id = db.Column(
        db.Integer, db.ForeignKey("season_sport_divisions.id"), nullable=False, index=True
    )
    home_team_id = db.Column(db.Integer, db.ForeignKey("season_teams.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("season_teams.id"), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    venue_key = db.Column(db.String(150), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    ends_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    result_status = db.Column(db.String(20), nullable=False, default="SCHEDULED", server_default="SCHEDULED")
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    finalized_at = db.Column(db.DateTime, nullable=True)
    finalized_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "season_sport_division_id": self.season_sport_division_id,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "venue": self.venue,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "result_status": self.result_status,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "finalized_at": self.finalized_at.isoformat() if self.finalized_at else None,
            "finalized_by": self.finalized_by,
        }


class GameResultReopening(db.Model):
    __tablename__ = "game_result_reopenings"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False, index=True)
    reason = db.Column(db.Text, nullable=False)
    reopened_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reopened_at = db.Column(db.DateTime, nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_score = db.Column(db.Integer, nullable=False)
    finalized_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    finalized_at = db.Column(db.DateTime, nullable=False)
