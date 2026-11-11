from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.users import User
from app.extensions import db


class UserRepository(BaseRepository):
    def get_by_id(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    def exists_by_username(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    def add(self, user: User) -> None:
        db.session.add(user)