from app.application.common.utils.base_classes import BaseRepository
from app.domain.models.roles import Role
from app.extensions import db


class RoleRepository(BaseRepository):
    def get_by_name(self, name: str) -> Role | None:
        return Role.query.filter_by(name=name).first()

    def add(self, role: Role) -> None:
        db.session.add(role)