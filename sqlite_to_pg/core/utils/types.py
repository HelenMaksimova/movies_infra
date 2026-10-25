from datetime import datetime, timezone
from typing import TypeVar

from dateutil import parser

__all__ = (
    "_Connection",
    "_Cursor",
    "convert_to_utc",
    "convert_to_uuid",
)

from uuid import UUID

_Connection = TypeVar("_Connection")
_Cursor = TypeVar("_Cursor")


def convert_to_utc(value: datetime | str) -> datetime:
    if isinstance(value, str):
        datetime_value = parser.parse(value)
    else:
        datetime_value = value

    return datetime_value.astimezone(timezone.utc)


def convert_to_uuid(value: str | UUID) -> UUID:
    if isinstance(value, str):
        return UUID(value)

    return value
