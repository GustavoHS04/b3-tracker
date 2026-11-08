import yfinance as yf
import pandas as pd


def buscar_historico(ticker: str, periodo: str = "1y") -> pd.DataFrame | None:
    df = yf.Ticker(ticker).history(period=periodo, auto_adjust=True)

    return df if not df.empty else None

def preparar_cotacoes(df: pd.DataFrame, ticker: str):
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

    df["data"] = df["data"].dt.date
    df["ticker"] = ticker

    return df[["ticker", "date", "open", "high", "low", "close", "volume"]]