from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class CreateSeasonSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    year = fields.Integer(required=True, validate=validate.Range(min=1))
    registration_start_date = fields.Date(allow_none=True, load_default=None)
    registration_end_date = fields.Date(allow_none=True, load_default=None)
    start_date = fields.Date(allow_none=True, load_default=None)
    end_date = fields.Date(allow_none=True, load_default=None)


class TransitionSeasonSchema(BaseSchema):
    season_status = fields.String(
        required=True,
        validate=validate.OneOf(["PLANNING", "REGISTRATION", "ONGOING", "COMPLETED", "ARCHIVED"]),
    )