from duckdb import DuckDBPyConnection

from .sources.yahoo import buscar_historico, buscar_nome, preparar_cotacoes
from .database.populate_db import populate_dim_ticker, save_quotes

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