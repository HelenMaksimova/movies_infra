from logging import Logger, config as log_config, getLogger
from os import environ
from typing import Literal

from core.app import (
    LOGGING_CONFIG,
    MoviePostgresSaver,
    MovieSQLiteLoader,
)


def load_from_sqlite(
    pg_settings: dict,
    sqlite_settings: str,
    table_names: list[str],
    pg_schema: str,
    logger: Logger,
    on_conflict: Literal["nothing", "update"] | None = "nothing",
):
    """Основной метод загрузки данных из SQLite в Postgres"""
    with (
        MovieSQLiteLoader(
            db_settings=sqlite_settings, batch_size=100, logger=logger
        ) as loader,
        MoviePostgresSaver(
            db_settings=pg_settings, db_schema=pg_schema, logger=logger
        ) as saver,
    ):
        data = loader.load_data(table_names)
        saver.save_data(data, on_conflict)


def get_settings() -> tuple[
    dict, str | None, str | None, Literal["nothing", "update"] | None
]:
    return (
        {
            "dbname": environ.get("POSTGRES_DB"),
            "user": environ.get("POSTGRES_USER"),
            "password": environ.get("POSTGRES_PASSWORD"),
            "host": environ.get("SQL_HOST"),
            "port": environ.get("SQL_PORT"),
        },
        environ.get("SQLITE_PATH"),
        environ.get("LOG_LEVEL"),
        environ.get("ON_CONFLICT"),
    )


if __name__ == "__main__":
    pg_settings, sqlite_settings, log_level, on_conflict = get_settings()

    log_config.dictConfig(LOGGING_CONFIG)
    logger = getLogger("db_transfer")
    logger.setLevel(log_level)

    load_from_sqlite(
        pg_settings,
        sqlite_settings,
        ["genre", "person", "film_work", "genre_film_work", "person_film_work"],
        "content",
        logger,
        on_conflict,
    )
