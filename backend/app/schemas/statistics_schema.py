from marshmallow import fields, validate

from app.schemas.base_schema import BaseSchema


class StatisticDefinitionSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    abbreviation = fields.String(required=True, validate=validate.Length(min=1, max=20))
    required = fields.Boolean(required=True)
    is_scoring = fields.Boolean(required=True)


class StatisticConfigurationSchema(BaseSchema):
    allow_team_points = fields.Boolean(required=True)
    types = fields.List(fields.Nested(StatisticDefinitionSchema), required=True, validate=validate.Length(min=1))


class ParticipantStatisticsSchema(BaseSchema):
    player_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    status = fields.String(required=True, allow_none=True, validate=validate.OneOf(["PLAYED", "DNP"]))
    values = fields.Dict(keys=fields.String(), values=fields.String(validate=validate.Length(max=40)), required=True)


class TeamStatisticsSchema(BaseSchema):
    team_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    team_points = fields.Integer(required=True, strict=True, allow_none=True,
                                 validate=validate.Range(min=0, max=2147483647))
    players = fields.List(fields.Nested(ParticipantStatisticsSchema), required=True)


class GameStatisticsSchema(BaseSchema):
    teams = fields.List(fields.Nested(TeamStatisticsSchema), required=True, validate=validate.Length(equal=2))
