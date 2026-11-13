from duckdb import DuckDBPyConnection
from collections import Counter
from enum import Enum
import pandas as pd
import logging

from .sources.yahoo import buscar_historico, buscar_nome, preparar_cotacoes
from .database.populate_db import populate_dim_ticker, save_quotes
from .database.queries import get_last_date, list_tickers, get_first_date

from .config import MAX_FALHAS_SEGUIDAS
from .errors import TickerNaoEncontradoError, FonteIndisponivelError

logger = logging.getLogger(__name__)

class Status(Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"


def _register_ticker(con: DuckDBPyConnection, ticker: str, nome: str, df: pd.DataFrame) -> None:
    con.begin()
    try:
        populate_dim_ticker(con, tickers=[(ticker,nome)])
        save_quotes(con, df)
        con.commit()

    except BaseException:
        con.rollback()
        raise

def _precisa_rebaixar(df: pd.DataFrame) -> bool:
    if (df["Dividends"] > 0).any() or (df["Stock Splits"] > 0).any():
        return True
    
    return False

def _normalize_ticker(raw: str) -> str:
    normalized = raw.strip().upper()
    if not normalized.endswith(".SA"):
        normalized += ".SA"

    return normalized

def add_tickers(con: DuckDBPyConnection, raws: str | list[str], periodo: str = "10y") -> dict[str, Status]:
    raws = [raws] if isinstance(raws, str) else raws
    results = {}
    tickers = []

    ordem = []
    for raw in raws:
        if not raw.strip():
            results[raw] = Status.NOT_FOUND
            ordem.append(raw)
        else:
            ticker = _normalize_ticker(raw)
            tickers.append(ticker)
            ordem.append(ticker)

    falhas = 0
    for i, ticker in enumerate(tickers):
        try:
            df = buscar_historico(ticker, periodo)

        except TickerNaoEncontradoError as e:
            logger.warning("Falha ao cadastrar: %s", e)
            results[ticker] = Status.NOT_FOUND
            falhas = 0
            continue
        except FonteIndisponivelError as e:
            logger.warning("Falha ao cadastrar: %s", e)
            results[ticker] = Status.UNAVAILABLE
            falhas += 1

            if falhas >= MAX_FALHAS_SEGUIDAS:
                restantes = tickers[i + 1:]
                logger.warning("Fonte indisponível %d vezes seguidas; pulando %d ativos", falhas, len(restantes))
                for rest in tickers[i + 1:]:
                    results[rest] = Status.UNAVAILABLE

                break

            continue

        nome = buscar_nome(ticker)
        df = preparar_cotacoes(df, ticker)

        _register_ticker(con, ticker, nome, df)        

        logger.info("Ticker %s cadastrado", ticker)
        results[ticker] = Status.OK
        falhas = 0

    return {k: results[k] for k in ordem}

def update_ticker(con: DuckDBPyConnection, ticker: str) -> Status:
    last = get_last_date(con, ticker)
    modo = "incremental" if last is not None else "inicial"

    try:
        df = buscar_historico(ticker, inicio=last)
        if last is not None and _precisa_rebaixar(df):
            first = get_first_date(con, ticker)
            df = buscar_historico(ticker, inicio=first)
            modo = "completo"

    except TickerNaoEncontradoError as e:
        logger.warning("Falha ao atualizar: %s", e)
        return Status.NOT_FOUND
    except FonteIndisponivelError as e:
        logger.warning("Falha ao atualizar: %s", e)
        return Status.UNAVAILABLE

    df = preparar_cotacoes(df, ticker)
    save_quotes(con, df)
    logger.debug("%s atualizado (%s): %d linhas", ticker, modo, len(df))
    return Status.OK

def update_all(con: DuckDBPyConnection) -> dict[str, Status]:
    tickers = list_tickers(con)
    results = {}
    falhas = 0

    logger.info("Atualizando %d ativos", len(tickers))
    for i, ticker in enumerate(tickers):
        status = update_ticker(con, ticker)
        results[ticker] = status

        if status is Status.UNAVAILABLE:
            falhas += 1
        else:
            falhas = 0

        if falhas >= MAX_FALHAS_SEGUIDAS:
            restantes = tickers[i + 1:]
            logger.warning("fonte indisponível %d vezes seguidas; pulando %d ativos", falhas, len(restantes))
            for rest in restantes:
                results[rest] = Status.UNAVAILABLE
            break

    logger.info("Resumo da atualização: %s", dict(Counter(s.name for s in results.values())))
    return results