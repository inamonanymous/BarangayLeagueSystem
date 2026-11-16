from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class RescheduleGameSchema(BaseSchema):
    venue = fields.String(required=True, validate=validate.Length(min=1, max=150))
    starts_at = fields.DateTime(required=True)
    ends_at = fields.DateTime(required=True)


class ScheduleGameSchema(RescheduleGameSchema):
    home_team_id = fields.Integer(required=True, validate=validate.Range(min=1))
    away_team_id = fields.Integer(required=True, validate=validate.Range(min=1))
