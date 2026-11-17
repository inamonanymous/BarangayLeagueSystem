from app.extensions import db

class SeasonSportDivision(db.Model):
    __tablename__ = "season_sport_divisions"

    id = db.Column(db.Integer, primary_key=True)
    season_sport_id = db.Column(db.Integer, db.ForeignKey("season_sports.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender_policy = db.Column(db.String(20), nullable=False, default="ANY")
    minimum_roster_size = db.Column(db.Integer, nullable=False)
    maximum_roster_size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    __table_args__ = (
        db.UniqueConstraint("season_sport_id", "name", name="uq_season_sport_division_name"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "season_sport_id": self.season_sport_id,
            "name": self.name,
            "gender_policy": self.gender_policy,
            "minimum_roster_size": self.minimum_roster_size,
            "maximum_roster_size": self.maximum_roster_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }