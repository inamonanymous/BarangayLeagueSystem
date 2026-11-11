from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class CreateUserSchema(BaseSchema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=100))
    password = fields.String(required=True, validate=validate.Length(min=8, max=128))
    role = fields.String(
        required=True,
        validate=validate.OneOf(["Administrator", "Encoder", "Viewer"]),
    )