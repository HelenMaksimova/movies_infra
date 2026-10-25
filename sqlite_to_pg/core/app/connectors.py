from core.app.dataclasses import (
    FilmWorkDC,
    GenreDC,
    GenreFilmWorkDC,
    PersonDC,
    PersonFilmWorkDC,
)
from core.utils import (
    BaseRecordDC,
    PostgresSaver,
    SQLiteLoader,
)

__all__ = (
    "MoviePostgresSaver",
    "MovieSQLiteLoader",
)


class MovieSQLiteLoader(SQLiteLoader):
    _RECORD_DC_TABLE_MAP: dict[str, type[BaseRecordDC]] = {
        "film_work": FilmWorkDC,
        "genre": GenreDC,
        "person": PersonDC,
        "genre_film_work": GenreFilmWorkDC,
        "person_film_work": PersonFilmWorkDC,
    }


class MoviePostgresSaver(PostgresSaver):
    _RECORD_DC_TABLE_MAP: dict[str, type[BaseRecordDC]] = {
        "film_work": FilmWorkDC,
        "genre": GenreDC,
        "person": PersonDC,
        "genre_film_work": GenreFilmWorkDC,
        "person_film_work": PersonFilmWorkDC,
    }
