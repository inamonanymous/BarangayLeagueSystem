from app.extensions import db

class Division(db.Model):
    __tablename__ = "divisions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    gender_policy = db.Column(
        db.Enum("ANY", "MALE_ONLY", "FEMALE_ONLY", "MIXED", name="gender_policy"),
        nullable=False,
        default="ANY",
    )
    minimum_roster_size = db.Column(db.Integer, nullable=False)
    maximum_roster_size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "gender_policy": self.gender_policy,
            "minimum_roster_size": self.minimum_roster_size,
            "maximum_roster_size": self.maximum_roster_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }