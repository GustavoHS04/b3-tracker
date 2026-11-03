import yfinance as yf
import pandas as pd

class DadosIndisponiveisisError(Exception):
    """Dados indisponíveis para este fundo."""

def buscar_historico(ticker: str, periodo: str = "1y"):
    df = yf.Ticker(ticker).history(period=periodo, auto_adjust=True)
    if df.empty:
        raise DadosIndisponiveisisError(f"dados indisponíveis para o ticker '{ticker}'.")
        
    return df

for ticker in ["PETR4.SA", "XXXX4.SA"]:
    try:
        df = buscar_historico(ticker)
        print(df.tail(3))
        print(df.columns)

    except DadosIndisponiveisisError as e:
        print(f"Erro: {e}")