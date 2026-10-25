from dataclasses import dataclass, fields
from datetime import datetime
from types import NoneType, UnionType
from typing import get_args
from uuid import UUID

from core.utils.types import convert_to_utc, convert_to_uuid

__all__ = ("BaseRecordDC",)


@dataclass
class BaseRecordDC:
    _FIELDS_MAP = {
        "created_at": "created",
        "updated_at": "modified",
    }
    _REVERSE_FIELDS_MAP = {value: key for key, value in _FIELDS_MAP.items()}
    _CONVERTERS_MAP = {
        UUID.__name__: convert_to_uuid,
        datetime.__name__: convert_to_utc,
    }

    @classmethod
    def from_dict(cls, data: dict) -> "BaseRecordDC":
        mapped_data = {
            cls._FIELDS_MAP.get(field_name, field_name): value
            for field_name, value in data.items()
        }

        return cls(**mapped_data)

    @classmethod
    @property
    def source_column_names(cls) -> tuple[str, ...]:
        return tuple(
            cls._REVERSE_FIELDS_MAP.get(field.name, field.name)
            for field in fields(cls)
        )

    def _clean_type(self, field_type: type | UnionType) -> str:
        if isinstance(field_type, UnionType):
            field_types = {type_ for type_ in get_args(field_type)}
            field_types.discard(NoneType)
            if len(field_types) == 1:
                return field_types.pop().__name__
            else:
                raise ValueError("Unavailable types for dataclass field")

        return field_type.__name__

    def __post_init__(self):
        for field in fields(self):
            converter = self._CONVERTERS_MAP.get(self._clean_type(field.type))
            if converter:
                setattr(self, field.name, converter(getattr(self, field.name)))
