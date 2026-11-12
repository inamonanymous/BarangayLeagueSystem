from app.extensions import db


class Roster(db.Model):
    __tablename__ = "rosters"

    id = db.Column(db.Integer, primary_key=True)
    season_team_id = db.Column(db.Integer, db.ForeignKey("season_teams.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    jersey_number = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.UniqueConstraint("season_team_id", "jersey_number", name="uq_roster_team_jersey"),
        db.UniqueConstraint("season_team_id", "player_id", name="uq_roster_team_player"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "season_team_id": self.season_team_id,
            "player_id": self.player_id,
            "jersey_number": self.jersey_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
