from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class AddRosterPlayerSchema(BaseSchema):
    player_id = fields.Integer(required=True, validate=validate.Range(min=1))
    jersey_number = fields.String(required=True, validate=validate.Length(min=1, max=10))
    voter_verified = fields.Boolean(missing=False)
    voter_number = fields.String(allow_none=True, validate=validate.Length(max=100))
    eligibility_notes = fields.String(allow_none=True)


class UpdateRosterSchema(BaseSchema):
    jersey_number = fields.String(required=True, validate=validate.Length(min=1, max=10))
