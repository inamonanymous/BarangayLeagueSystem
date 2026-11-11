from app.extensions import db

class SeasonSport(db.Model):
    __tablename__ = "season_sports"

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("seasons.id"), nullable=False)
    sport_id = db.Column(db.Integer, db.ForeignKey("sports.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    __table_args__ = (
        db.UniqueConstraint("season_id", "sport_id", name="uq_season_sport"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "season_id": self.season_id,
            "sport_id": self.sport_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }