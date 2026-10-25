from enum import Enum

__all__ = (
    "FilmWorkTypeEnum",
    "PersonRoleEnum",
)


class _BaseEnum(Enum):
    @classmethod
    @property
    def values(cls):
        return {member.value for member in cls}

    @classmethod
    @property
    def names(cls):
        return {member.name for member in cls}


class PersonRoleEnum(_BaseEnum):
    actor = "actor"
    director = "director"
    writer = "writer"


class FilmWorkTypeEnum(_BaseEnum):
    movie = "movie"
    tv_show = "tv show"
