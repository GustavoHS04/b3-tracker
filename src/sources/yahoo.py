import yfinance as yf
import pandas as pd
from datetime import date

def buscar_historico(ticker: str, periodo: str = "10y", inicio: date | None = None) -> pd.DataFrame | None:
    if inicio is None:
        df = yf.Ticker(ticker).history(period=periodo, auto_adjust=True)
    else:
        df = yf.Ticker(ticker).history(start=inicio, auto_adjust=True)

    return df if not df.empty else None

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
    info = yf.Ticker(ticker).info

    return info.get("longName") or info.get("shortName") or ticker