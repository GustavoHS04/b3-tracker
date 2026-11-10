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

def populate_dim_ticker(con: DuckDBPyConnection, ticker: list[tuple[str, str]]) -> None:
    df = pd.DataFrame(ticker, columns=["ticker", "name"])

    con.execute("""
        INSERT OR IGNORE INTO dim_ticker (ticker, name)
        SELECT ticker, name FROM df
    """)

def save_quotes(con: DuckDBPyConnection, df: pd.DataFrame) -> None:
    con.execute("""
        INSERT OR REPLACE INTO daily_quotes (ticker, date, open, high, low, close, volume)
        SELECT ticker, date, open, high, low, close, volume FROM df
    """)