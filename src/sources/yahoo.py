import yfinance as yf
import pandas as pd
from datetime import date
import logging

from yfinance.exceptions import YFRateLimitError, YFTickerMissingError
from curl_cffi.requests.exceptions import HTTPError, RequestException

from ..errors import TickerNaoEncontradoError, FonteIndisponivelError

logger = logging.getLogger(__name__)
#configura para o yf não ignorar erros
yf.config.debug.hide_exceptions = False

def buscar_historico(ticker: str, periodo: str = "10y", inicio: date | None = None) -> pd.DataFrame:
    try:
        if inicio is None:
            df = yf.Ticker(ticker).history(period=periodo, auto_adjust=True)
        else:
            df = yf.Ticker(ticker).history(start=inicio, auto_adjust=True)
    except YFTickerMissingError as e:
        raise TickerNaoEncontradoError(f"Ticker '{ticker}' não encontrado.") from e
    except HTTPError as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status == 404:
            raise TickerNaoEncontradoError(f"Ticker '{ticker}' não encontrado.") from e
        raise FonteIndisponivelError(f"Yahoo Finance indisponível ao buscar '{ticker}' (HTTP {status}).") from e
    except (YFRateLimitError, RequestException) as e:
        raise FonteIndisponivelError(f"Yahoo Finance indisponível ao buscar '{ticker}' ({type(e).__name__}).") from e
    if df.empty:
        raise TickerNaoEncontradoError(f"Nenhum dado retornado para '{ticker}'.")
    
    return df

def preparar_cotacoes(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    df = df.reset_index()
    df = df.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    df["date"] = df["date"].dt.date
    df["ticker"] = ticker

    return df[["ticker", "date", "open", "high", "low", "close", "volume"]]

def buscar_nome(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
    except (YFRateLimitError, RequestException):
        logger.warning("Nome de %s indisponível; usando o ticker como nome", ticker)
        return ticker
    
    return info.get("longName") or info.get("shortName") or ticker