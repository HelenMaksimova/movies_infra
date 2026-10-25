from logging import INFO, basicConfig, getLogger
from os import environ
from typing import Dict, Optional, Tuple

from psycopg import connect as pg_connect
from psycopg.connection import Connection
from psycopg.errors import Error as PsycopgError

basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

SQL_QUERIES: Dict[str, str] = {
    "film_work": """
        CREATE TABLE IF NOT EXISTS content.film_work (
            created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            id UUID PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            creation_date DATE,
            rating FLOAT,
            type VARCHAR(255) NOT NULL DEFAULT 'movie'
        );
        CREATE INDEX IF NOT EXISTS film_work_rating_idx ON content.film_work (rating);
        CREATE INDEX IF NOT EXISTS film_work_title_date_idx ON content.film_work (title, creation_date);
    """,
    "genre": """
        CREATE TABLE IF NOT EXISTS content.genre (
            created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT
        );
    """,
    "person": """
        CREATE TABLE IF NOT EXISTS content.person (
            created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            id UUID PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS person_full_name_idx ON content.person (full_name);
    """,
    "genre_film_work": """
        CREATE TABLE IF NOT EXISTS content.genre_film_work (
            id UUID PRIMARY KEY,
            created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            film_work_id UUID NOT NULL,
            genre_id UUID NOT NULL,
            CONSTRAINT unique_film_work_genre UNIQUE (film_work_id, genre_id),
            CONSTRAINT fk_genre_film_work_film_work FOREIGN KEY (film_work_id) REFERENCES content.film_work(id) ON DELETE CASCADE,
            CONSTRAINT fk_genre_film_work_genre FOREIGN KEY (genre_id) REFERENCES content.genre(id) ON DELETE CASCADE
        );
    """,
    "person_film_work": """
        CREATE TABLE IF NOT EXISTS content.person_film_work (
            id UUID PRIMARY KEY,
            role VARCHAR(16) NOT NULL DEFAULT 'actor',
            created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            film_work_id UUID NOT NULL,
            person_id UUID NOT NULL,
            CONSTRAINT unique_film_work_person_role UNIQUE (film_work_id, person_id, role),
            CONSTRAINT fk_person_film_work_film_work FOREIGN KEY (film_work_id) REFERENCES content.film_work(id) ON DELETE CASCADE,
            CONSTRAINT fk_person_film_work_person FOREIGN KEY (person_id) REFERENCES content.person(id) ON DELETE CASCADE
        );
    """,
}


def table_exists(conn: Connection, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'content' AND table_name = %s
            )
        """,
            (table_name,),
        )
        result: Tuple[bool] = cur.fetchone()
        return result[0] if result else False


def create_table(conn: Connection, table_name: str, sql: str) -> None:
    try:
        if table_exists(conn, table_name):
            logger.info(f"Table '{table_name}' already exists, skipping")
            return

        with conn.cursor() as cur:
            cur.execute(sql)

        logger.info(f"Table '{table_name}' created successfully")
    except PsycopgError as e:
        logger.error(f"Failed to create table '{table_name}': {e}")


def get_connection_params() -> Optional[Dict[str, str]]:
    required = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]

    if missing := [var for var in required if not environ.get(var)]:
        logger.error(f"Missing required env vars: {', '.join(missing)}")
        return None

    return {
        "host": environ.get("SQL_HOST", "localhost"),
        "port": environ.get("SQL_PORT", "5432"),
        "dbname": environ["POSTGRES_DB"],
        "user": environ["POSTGRES_USER"],
        "password": environ["POSTGRES_PASSWORD"],
    }


def main() -> None:
    conn_params: Optional[Dict[str, str]] = get_connection_params()
    if conn_params is None:
        return

    logger.info(
        f"Connecting to database '{conn_params['dbname']}' at {conn_params['host']}:{conn_params['port']}"
    )

    try:
        with pg_connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS content;")

            for table_name, sql in SQL_QUERIES.items():
                create_table(conn, table_name, sql)

    except PsycopgError as e:
        logger.error(f"Database connection failed: {e}")
        return


if __name__ == "__main__":
    main()
