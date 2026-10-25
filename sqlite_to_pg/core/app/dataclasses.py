from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from core.app.enums import (
    FilmWorkTypeEnum,
    PersonRoleEnum,
)
from core.utils.dataclasses import BaseRecordDC

__all__ = (
    "FilmWorkDC",
    "GenreDC",
    "GenreFilmWorkDC",
    "PersonDC",
    "PersonFilmWorkDC",
)


@dataclass
class GenreDC(BaseRecordDC):
    name: str
    created: datetime
    description: str | None = None
    id: UUID = field(default_factory=uuid4)
    modified: datetime | None = None


@dataclass
class PersonDC(BaseRecordDC):
    full_name: str
    created: datetime
    id: UUID = field(default_factory=uuid4)
    modified: datetime | None = None


@dataclass
class FilmWorkDC(BaseRecordDC):
    title: str
    type: str
    created: datetime
    creation_date: date | None = None
    rating: float | None = None
    description: str | None = None
    id: UUID = field(default_factory=uuid4)
    modified: datetime | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.type not in FilmWorkTypeEnum.values:
            raise ValueError(f"Invalid type: {self.type}")


@dataclass
class GenreFilmWorkDC(BaseRecordDC):
    film_work_id: UUID
    genre_id: UUID
    created: datetime
    id: UUID = field(default_factory=uuid4)


@dataclass
class PersonFilmWorkDC(BaseRecordDC):
    film_work_id: UUID
    person_id: UUID
    created: datetime
    id: UUID = field(default_factory=uuid4)
    role: str = field(default=PersonRoleEnum.actor.value)

    def __post_init__(self):
        super().__post_init__()
        if self.role in PersonRoleEnum.names:
            self.role = PersonRoleEnum[self.role].value
        elif self.role not in PersonRoleEnum.values:
            raise ValueError(f"Invalid role: {self.role}")
