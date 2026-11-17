from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class RescheduleGameSchema(BaseSchema):
    venue = fields.String(required=True, validate=validate.Length(min=1, max=150))
    starts_at = fields.DateTime(required=True)
    ends_at = fields.DateTime(required=True)


class ScheduleGameSchema(RescheduleGameSchema):
    home_team_id = fields.Integer(required=True, validate=validate.Range(min=1))
    away_team_id = fields.Integer(required=True, validate=validate.Range(min=1))


class GameResultSchema(BaseSchema):
    home_score = fields.Integer(required=True, strict=True, validate=validate.Range(min=0, max=2147483647))
    away_score = fields.Integer(required=True, strict=True, validate=validate.Range(min=0, max=2147483647))


class ReopenGameSchema(BaseSchema):
    reason = fields.String(required=True, validate=validate.Length(min=1, max=2000))
