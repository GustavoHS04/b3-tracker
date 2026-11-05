import duckdb

from ..config import DATABASE_PATH
def connect(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(DATABASE_PATH, read_only=read_only)

    return con