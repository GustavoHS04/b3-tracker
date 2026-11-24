import pandas as pd
from duckdb import DuckDBPyConnection

NOMES_DIAS = {
    0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
    4: "friday", 5: "saturday", 6: "sunday",
}

def populate_dim_date(con: DuckDBPyConnection, inicio: str, fim: str) -> None:
    datas = pd.date_range(start=inicio, end=fim, freq="D")

    df = pd.DataFrame({"date": datas})
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["week_day"] = df["date"].dt.dayofweek.map(NOMES_DIAS)

    con.execute("""
        INSERT OR IGNORE INTO dim_date (date, year, month, week_day)
        SELECT CAST(date AS DATE), year, month, week_day FROM df
    """)

def populate_dim_ticker(con: DuckDBPyConnection, tickers: list[tuple[str, str]]) -> None:
    df = pd.DataFrame(tickers, columns=["ticker", "name"])

    con.execute("""
        INSERT OR IGNORE INTO dim_ticker (ticker, name)
        SELECT ticker, name FROM df
    """)

def save_quotes(con: DuckDBPyConnection, df: pd.DataFrame) -> None:
    con.execute("""
        INSERT INTO daily_quotes (ticker, date, open, high, low, close, volume)
        (
            SELECT
                ticker,
                date,
                CASE WHEN open > 0 THEN open    END,
                CASE WHEN open > 0 THEN high    END,
                CASE WHEN open > 0 THEN low     END,
                close,
                CASE WHEN open > 0 THEN volume  END,
            FROM df
        )
        ON CONFLICT (ticker, date) DO UPDATE SET
            open    = COALESCE(EXCLUDED.open, open),
            high    = COALESCE(EXCLUDED.high, high),
            low     = COALESCE(EXCLUDED.low, low),
            close   = COALESCE(EXCLUDED.close, close),
            volume  = COALESCE(EXCLUDED.volume, volume)
    """)

def delete_quotes(con: DuckDBPyConnection, ticker: str) -> None:
    con.execute("DELETE from daily_quotes WHERE ticker = ?", [ticker])

def delete_ticker(con: DuckDBPyConnection, ticker: str) -> None:
    con.execute("DELETE from dim_ticker WHERE ticker = ?", [ticker])