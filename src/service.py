from duckdb import DuckDBPyConnection
import pandas as pd

from .sources.yahoo import buscar_historico, buscar_nome, preparar_cotacoes
from .database.populate_db import populate_dim_ticker, save_quotes
from .database.queries import get_last_date, list_tickers, get_first_date

def _precisa_rebaixar(df: pd.DataFrame) -> bool:
    if (df["Dividends"] > 0).any() or (df["Stock Splits"] > 0).any():
        return True
    
    return False

def _normalize_ticker(raw: str) -> str:
    normalized = raw.strip().upper()
    if not normalized.endswith(".SA"):
        normalized += ".SA"

    return normalized

def add_tickers(con: DuckDBPyConnection, raws: str | list[str], periodo: str = "10y") -> dict[str, bool]:
    raws = [raws] if isinstance(raws, str) else raws
    results = {}

    for raw in raws:
        if not raw.strip():
            results[raw] = False
            continue

        ticker = _normalize_ticker(raw)
        df = buscar_historico(ticker, periodo)
        if df is None:
            results[ticker] = False
            continue

        nome = buscar_nome(ticker)
        populate_dim_ticker(con, [(ticker, nome)])

        df = preparar_cotacoes(df, ticker)
        save_quotes(con, df)

        results[ticker] = True

    return results

def update_ticker(con: DuckDBPyConnection, ticker: str) -> bool:
    last = get_last_date(con, ticker)
    df = buscar_historico(ticker, inicio=last)
    if df is None:
        return False

    if last is not None and _precisa_rebaixar(df):
        first = get_first_date(con, ticker)
        df = buscar_historico(ticker, inicio=first)
        if df is None:
            return False
        
    df = preparar_cotacoes(df, ticker)
    save_quotes(con, df)

    return True

def update_all(con: DuckDBPyConnection) -> dict[str, bool]:
    tickers = list_tickers(con)
    results = {}
    for ticker in tickers:
        result = update_ticker(con, ticker)

        results[ticker] = result

    return results