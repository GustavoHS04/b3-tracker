from duckdb import DuckDBPyConnection

def _create_dim_data(con: DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_data (
            data        DATE PRIMARY KEY,
            ano         INTEGER,
            mes         INTEGER,
            dia_semana  VARCHAR
        )
    """)

def _create_cotacoes_diarias(con: DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS cotacoes_diarias (
            ticker  VARCHAR NOT NULL,
            data    DATE    NOT NULL,
            open    DOUBLE,
            high    DOUBLE,
            low     DOUBLE,
            close   DOUBLE,
            volume  BIGINT,
            PRIMARY KEY (ticker, data),
            FOREIGN KEY (data) REFERENCES dim_data (data)
        )
    """)


def create(con: DuckDBPyConnection) -> None:
    _create_dim_data(con)
    _create_cotacoes_diarias(con)