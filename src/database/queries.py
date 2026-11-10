from duckdb import DuckDBPyConnection
from datetime import date


def get_last_date(con: DuckDBPyConnection, ticker: str) -> date | None:
    row = con.execute("SELECT max(date) FROM daily_quotes WHERE ticker = ?", [ticker]).fetchone()

    return row[0] if row is not None else None

def list_tickers(con: DuckDBPyConnection) -> list[str]:
    rows = con.execute("SELECT ticker FROM dim_ticker ORDER BY ticker").fetchall()

    return [row[0] for row in rows] 