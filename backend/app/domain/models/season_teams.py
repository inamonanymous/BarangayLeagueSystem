from app.extensions import db


class SeasonTeam(db.Model):
    __tablename__ = "season_teams"

    id = db.Column(db.Integer, primary_key=True)
    season_sport_division_id = db.Column(
        db.Integer,
        db.ForeignKey("season_sport_divisions.id"),
        nullable=False,
    )
    name = db.Column(db.String(150), nullable=False)
    barangay = db.Column(db.String(150), nullable=False)
    coach_name = db.Column(db.String(150), nullable=True)
    manager_name = db.Column(db.String(150), nullable=True)
    team_color = db.Column(db.String(50), nullable=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    archived_at = db.Column(db.DateTime, nullable=True)
    archived_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "season_sport_division_id",
            "name",
            name="uq_season_team_division_name",
        ),
    )


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "season_sport_division_id": self.season_sport_division_id,
            "name": self.name,
            "barangay": self.barangay,
            "coach_name": self.coach_name,
            "manager_name": self.manager_name,
            "team_color": self.team_color,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
