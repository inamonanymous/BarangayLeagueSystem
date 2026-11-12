from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class PlayerFieldsSchema(BaseSchema):
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    middle_name = fields.String(allow_none=True, missing=None)
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    birthdate = fields.Date(required=True)
    gender = fields.String(required=True, validate=validate.Length(min=1, max=20))
    address = fields.String(required=True, validate=validate.Length(min=1, max=1000))


class CreatePlayerSchema(PlayerFieldsSchema):
    pass


class UpdatePlayerSchema(PlayerFieldsSchema):
    pass


class ArchivePlayerSchema(BaseSchema):
    is_archived = fields.Boolean(required=True)
