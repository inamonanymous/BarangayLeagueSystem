from datetime import date
from typing import TypedDict


class PlayerValues(TypedDict):
    first_name: str
    middle_name: str
    last_name: str
    birthdate: date
    gender: str
    address: str


class VoterIdData(TypedDict):
    year: int
    voter_number: str


class PlayerData(TypedDict):
    id: int
    first_name: str
    middle_name: str | None
    last_name: str
    birthdate: str
    gender: str
    address: str
    is_archived: bool
    created_at: str | None
    updated_at: str | None
