from duckdb import DuckDBPyConnection

def _create_dim_date(con: DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_date (
            date      DATE PRIMARY KEY,
            year      INTEGER,
            month     INTEGER,
            week_day  VARCHAR
        )
    """)

def _create_dim_ticker(con: DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_ticker (
            ticker VARCHAR PRIMARY KEY,
            name   VARCHAR
        )
    """)

def _create_daily_quotes(con: DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS daily_quotes (
            ticker  VARCHAR NOT NULL,
            date    DATE    NOT NULL,
            open    DOUBLE,
            high    DOUBLE,
            low     DOUBLE,
            close   DOUBLE,
            volume  BIGINT,
            PRIMARY KEY (ticker, date),
            FOREIGN KEY (date) REFERENCES dim_date (date),
            FOREIGN KEY (ticker) REFERENCES dim_ticker (ticker)
        )
    """)


def create(con: DuckDBPyConnection) -> None:
    _create_dim_date(con)
    _create_dim_ticker(con)
    _create_daily_quotes(con)