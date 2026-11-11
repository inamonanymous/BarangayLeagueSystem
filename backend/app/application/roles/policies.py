from app.application.common.utils.base_classes import BasePolicy


ROLE_DESCRIPTIONS = {
    "Administrator": "System administrator",
    "Encoder": "League game and statistics encoder",
    "Viewer": "Read-only league viewer",
}


class RolePolicy(BasePolicy):
    def description_for(self, role_name: str) -> str:
        try:
            return ROLE_DESCRIPTIONS[role_name]
        except KeyError as exc:
            raise ValueError("Role is not supported.") from exc