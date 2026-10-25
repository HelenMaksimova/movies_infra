from contextlib import closing
from dataclasses import astuple, fields
from logging import Logger
from sqlite3 import (
    Connection as SQLiteConnection,
    Cursor as SQLiteCursor,
    Error as SQLiteError,
    Row as SQLiteRow,
    connect as sqlite_connect,
)
from typing import Any, Generator, Generic, Iterable, Literal

from psycopg import (
    Connection as PGConnection,
    Cursor as PGCursor,
    Error as PGError,
    connect as pg_connect,
)
from psycopg.sql import SQL, Composed, Identifier, Placeholder

from core.utils.dataclasses import BaseRecordDC
from core.utils.types import _Connection, _Cursor

__all__ = (
    "PostgresSaver",
    "SQLDatabaseConnector",
    "SQLiteLoader",
)


class SQLDatabaseConnector(Generic[_Connection, _Cursor]):
    _RECORD_DC_TABLE_MAP: dict[str, type[BaseRecordDC]] | None = None

    def __init__(
        self,
        connection: _Connection | None = None,
        db_settings: dict | str | None = None,
        logger: Logger | None = None,
        db_schema: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        if not (connection or db_settings):
            raise ValueError(
                "One of parameters must be specified: connection, db_settings"
            )
        self._logger = logger
        self._connection = connection or self._create_connection(db_settings)
        self._db_schema = db_schema
        self._batch_size = batch_size

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass

    @property
    def connection(self) -> _Connection:
        return self._connection

    @property
    def db_schema(self) -> str | None:
        return self._db_schema

    @property
    def logger(self) -> Logger | None:
        if not self._logger:
            raise ValueError("logger parameter must be specified")

        return self._logger

    @property
    def batch_size(self) -> int | None:
        if not self._batch_size:
            raise ValueError("batch_size parameter must be specified")

        return self._batch_size

    @property
    def record_dc_table_map(self) -> dict[str, type[BaseRecordDC]]:
        if self._RECORD_DC_TABLE_MAP is None:
            raise ValueError("record_dc_table_map parameter must be specified")

        return self._RECORD_DC_TABLE_MAP

    def _create_connection(self, db_settings: dict | str) -> _Connection:
        raise NotImplementedError


class SQLiteLoader(SQLDatabaseConnector[SQLiteConnection, SQLiteCursor]):
    def __exit__(self, *exc_info):
        try:
            if self.connection:
                self.connection.close()
        except SQLiteError as err:
            self.logger.error("SQLite connection closing error: %s", err)

    def _create_connection(self, db_settings: str) -> SQLiteConnection:
        try:
            connection = sqlite_connect(db_settings)
            connection.row_factory = SQLiteRow
            return connection
        except SQLiteError as err:
            self.logger.error("SQLite create connection error: %s", err)
            raise

    def _extract_data(
        self, db_cursor: SQLiteCursor, query: str
    ) -> Generator[list[SQLiteRow], None, None]:
        db_cursor.execute(query)

        while results := db_cursor.fetchmany(self.batch_size):
            yield results

    def _converse_to_dc(
        self, record_dc: type[BaseRecordDC], row: SQLiteRow
    ) -> BaseRecordDC | None:
        try:
            data = dict(row)
            return record_dc.from_dict(data)
        except (ValueError, AttributeError, TypeError) as err:
            self.logger.warning(
                "Record with data: %s could not converse to dataclass with error: %s",
                data,
                err,
            )

    def _load_data(
        self, query: str, record_dc: type[BaseRecordDC]
    ) -> Generator[list[BaseRecordDC], None, None]:
        try:
            with self.connection as conn, closing(conn.cursor()) as db_cursor:
                extracted_data = self._extract_data(db_cursor, query)
                for data in extracted_data:
                    yield [
                        record
                        for row in data
                        if (record := self._converse_to_dc(record_dc, row))
                    ]
        except SQLiteError as err:
            self.logger.error(
                "Data weren't loaded from SQLite with error: %s", err
            )
            raise

    def _get_query(self, table_name: str, columns: Iterable[str] | None) -> str:
        columns_str = ", ".join(columns) if columns else "*"
        schema_str = f"{self.db_schema}." if self.db_schema else ""
        query = f"SELECT {schema_str}{columns_str} FROM {table_name};"

        self.logger.info("[SQL] %s", query)
        return query

    def load_data(
        self,
        table_names: Iterable[str],
    ) -> dict[str, Generator[list[BaseRecordDC], None, None]]:
        result_data = {}
        for table_name in table_names:
            try:
                record_dc = self.record_dc_table_map[table_name]
                query = self._get_query(
                    table_name, record_dc.source_column_names
                )
                data = self._load_data(query, record_dc)
                result_data[table_name] = data
                self.logger.info(
                    "Data was preloaded from SQLite database table: %s",
                    table_name,
                )
            except KeyError:
                self.logger.error(
                    "There is not table name: %s in available table names",
                    table_name,
                )

        return result_data


class PostgresSaver(SQLDatabaseConnector[PGConnection, PGCursor]):
    def __exit__(self, *exc_info):
        try:
            if self.connection:
                self.connection.close()
        except SQLiteError as err:
            self.logger.error("Postgres connection closing error: %s", err)

    def _create_connection(self, db_settings: dict) -> PGConnection:
        try:
            connection = pg_connect(**db_settings)
            return connection
        except PGError as err:
            self.logger.error("Postgres create connection error: %s", err)
            raise

    def _construct_data(
        self, record_dc: BaseRecordDC
    ) -> tuple[Any, ...] | None:
        try:
            return astuple(record_dc)
        except TypeError as err:
            self.logger.warning(
                "Record: %s could not converse to tuple with error: %s",
                record_dc,
                err,
            )

    def _save_data(
        self,
        query: str | SQL | Composed,
        data: Generator[list[BaseRecordDC], None, None],
        db_cursor: PGCursor,
    ) -> None:
        for records in data:
            record_data = tuple(
                conversed_data
                for record in records
                if (conversed_data := self._construct_data(record))
            )
            try:
                db_cursor.executemany(query, record_data)
            except PGError as err:
                self.logger.error(
                    "Data weren't saved into Postgres with error: %s", err
                )
                raise

    def _get_query(
        self,
        table_name: str,
        columns: tuple[str, ...],
        on_conflict: Literal["nothing", "update"] = "nothing",
    ) -> Composed:
        columns_str = SQL(", ").join(Identifier(column) for column in columns)
        values_placeholders = SQL(", ").join([Placeholder()] * len(columns))
        query = SQL(
            """INSERT INTO {schema}.{table} ({columns}) VALUES ({values})"""
        ).format(
            schema=Identifier(self.db_schema or "public"),
            table=Identifier(table_name),
            columns=columns_str,
            values=values_placeholders,
        )

        if on_conflict == "nothing":
            query = SQL("{query} ON CONFLICT (id) DO NOTHING").format(
                query=query
            )
        elif on_conflict == "update":
            update_set = SQL(", ").join(
                [
                    SQL("{column} = EXCLUDED.{column}").format(
                        column=Identifier(column)
                    )
                    for column in columns
                ]
            )
            query = SQL(
                "{query} ON CONFLICT (id) DO UPDATE SET {updates}"
            ).format(query=query, updates=update_set)

        self.logger.info("[SQL] %s", query.as_string(self.connection))
        return query

    def save_data(
        self,
        record_data: dict[str, Generator[list[BaseRecordDC], None, None]],
        on_conflict: Literal["nothing", "update"] = "nothing",
    ) -> None:
        with self.connection as conn, closing(conn.cursor()) as db_cursor:
            for table_name, data in record_data.items():
                try:
                    columns = tuple(
                        field.name
                        for field in fields(
                            self.record_dc_table_map[table_name]
                        )
                    )
                    query = self._get_query(table_name, columns, on_conflict)
                    self._save_data(query, data, db_cursor)
                    self.logger.info(
                        "Data was saved to Postgres database table: %s",
                        table_name,
                    )
                except KeyError:
                    self.logger.error(
                        "There is not table name: %s in available table names",
                        table_name,
                    )
