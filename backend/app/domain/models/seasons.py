from app.extensions import db

class Season(db.Model):
    __tablename__ = "seasons"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    registration_start_date = db.Column(db.Date, nullable=True)
    registration_end_date = db.Column(db.Date, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    season_status = db.Column(db.Enum("PLANNING", "REGISTRATION", "ONGOING", "COMPLETED", "ARCHIVED", name="season_status"), nullable=False, default="PLANNING")
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "registration_start_date": self.registration_start_date.isoformat() if self.registration_start_date else None,
            "registration_end_date": self.registration_end_date.isoformat() if self.registration_end_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "season_status": self.season_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }