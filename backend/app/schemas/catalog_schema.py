from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class CreateSportSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(allow_none=True)


class CreateDivisionSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    gender_policy = fields.String(
        validate=validate.OneOf(["ANY", "MALE_ONLY", "FEMALE_ONLY", "MIXED"]),
    )
    minimum_roster_size = fields.Integer(required=True, validate=validate.Range(min=1))
    maximum_roster_size = fields.Integer(required=True, validate=validate.Range(min=1))
    minimum_age_limit = fields.Integer(required=True, validate=validate.Range(min=0))
    maximum_age_limit = fields.Integer(required=True, validate=validate.Range(min=0))
