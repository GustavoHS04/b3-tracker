from duckdb import DuckDBPyConnection
from datetime import date
import pandas as pd

def get_first_date(con: DuckDBPyConnection, ticker: str) -> date | None:
    row = con.execute("SELECT min(date) FROM daily_quotes WHERE ticker = ?", [ticker]).fetchone()

    return row[0] if row is not None else None

def get_last_date(con: DuckDBPyConnection, ticker: str) -> date | None:
    row = con.execute("SELECT max(date) FROM daily_quotes WHERE ticker = ?", [ticker]).fetchone()

    return row[0] if row is not None else None

def list_tickers(con: DuckDBPyConnection) -> list[str]:
    rows = con.execute("SELECT ticker FROM dim_ticker ORDER BY ticker").fetchall()

    return [row[0] for row in rows]

def get_indicators(con: DuckDBPyConnection, ticker: str, window: int = 20) -> pd.DataFrame:
    if window < 1:
        raise ValueError("window precisa ser >= 1")
    
    result = con.execute(f"""
        SELECT
            date,
            close,
            close/lag(close) OVER(PARTITION BY ticker ORDER BY date) - 1 AS daily_return,
            avg(close) OVER(
                PARTITION BY ticker
                ORDER BY date
                ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW
            ) AS moving_avg
        FROM daily_quotes
        WHERE ticker = ?
        ORDER BY date
    """, [ticker]).df()

    return result