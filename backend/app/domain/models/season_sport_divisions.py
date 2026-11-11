from app.extensions import db

class SeasonSportDivision(db.Model):
    __tablename__ = "season_sport_divisions"

    id = db.Column(db.Integer, primary_key=True)
    season_sport_id = db.Column(db.Integer, db.ForeignKey("season_sports.id"), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("divisions.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    __table_args__ = (
        db.UniqueConstraint("season_sport_id", "division_id", name="uq_season_sport_division"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "season_sport_id": self.season_sport_id,
            "division_id": self.division_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }