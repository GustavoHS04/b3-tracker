import pandas as pd
from duckdb import DuckDBPyConnection

NOMES_DIAS = {
    0: "segunda", 1: "terça", 2: "quarta", 3: "quinta",
    4: "sexta", 5: "sábado", 6: "domingo",
}
def populate_dim_data(con: DuckDBPyConnection, inicio: str, fim: str) -> None:
    datas = pd.date_range(start=inicio, end=fim, freq="D")

    df = pd.DataFrame({"data": datas})
    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month
    df["dia_semana"] = df["data"].dt.dayofweek.map(NOMES_DIAS)

    con.execute("""
        INSERT OR IGNORE INTO dim_data (data, ano, mes, dia_semana)
        SELECT CAST(data AS DATE), ano, mes, dia_semana FROM df
    """)