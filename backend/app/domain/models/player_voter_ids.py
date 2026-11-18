from app.extensions import db


class PlayerVoterId(db.Model):
    __tablename__ = "player_voter_ids"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    voter_number = db.Column(db.String(100), nullable=False)
    normalized_number = db.Column(db.String(200), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("player_id", "year", name="uq_player_voter_id_year"),
        db.UniqueConstraint("year", "normalized_number", name="uq_voter_id_year_number"),
    )
