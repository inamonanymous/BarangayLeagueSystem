from sqlalchemy.exc import IntegrityError

from app.application.common.utils.base_classes import BaseService
from app.application.roles.policies import RolePolicy
from app.application.users.policies import UserPolicy
from app.domain.models.roles import Role
from app.domain.models.users import User
from app.extensions import db
from app.infrastructure.database.role_repository import RoleRepository
from app.infrastructure.database.user_repository import UserRepository


class UserService(BaseService):
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        role_repository: RoleRepository | None = None,
        user_policy: UserPolicy | None = None,
        role_policy: RolePolicy | None = None,
    ) -> None:
        self.user_repository = user_repository or UserRepository()
        self.role_repository = role_repository or RoleRepository()
        self.user_policy = user_policy or UserPolicy()
        self.role_policy = role_policy or RolePolicy()

    def create_user(self, username: str, password: str, role_name: str) -> User:
        username = self.user_policy.normalize_username(username)
        self.user_policy.validate_password(password)
        role_description = self.role_policy.description_for(role_name)

        if self.user_repository.exists_by_username(username):
            raise ValueError("A user with that username already exists.")

        role = self.role_repository.get_by_name(role_name)
        if role is None:
            role = Role(name=role_name, description=role_description)
            self.role_repository.add(role)

        user = User(username=username, is_active=True, role_obj=role)
        user.set_password(password)
        self.user_repository.add(user)

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise ValueError("A user with that username already exists.") from exc

        return user