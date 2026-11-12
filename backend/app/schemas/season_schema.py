from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class CreateSeasonSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    year = fields.Integer(required=True, validate=validate.Range(min=1))
    registration_start_date = fields.Date(allow_none=True)
    registration_end_date = fields.Date(allow_none=True)
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)


class TransitionSeasonSchema(BaseSchema):
    season_status = fields.String(
        required=True,
        validate=validate.OneOf(["PLANNING", "REGISTRATION", "ONGOING", "COMPLETED", "ARCHIVED"]),
    )