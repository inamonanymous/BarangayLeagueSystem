from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class RegisterSeasonTeamSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    barangay = fields.String(required=True, validate=validate.Length(min=1, max=150))
    coach_name = fields.String(allow_none=True, validate=validate.Length(max=150))
    manager_name = fields.String(allow_none=True, validate=validate.Length(max=150))
    team_color = fields.String(allow_none=True, validate=validate.Length(max=50))


class UpdateSeasonTeamSchema(RegisterSeasonTeamSchema):
    pass


class ArchiveSeasonTeamSchema(BaseSchema):
    is_archived = fields.Boolean(required=True)
