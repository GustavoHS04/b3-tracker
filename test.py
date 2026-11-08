from src.database.create_db import create
from src.database.populate_db import populate_dim_data
from src.database.connect_db import connect
from src.sources.yahoo import buscar_historico, preparar_cotacoes

from src.config import DATA_INICIO, DATA_FIM

def main():
    con = connect(read_only=False)

    create(con)
    
    test_populate(con, DATA_INICIO, DATA_FIM)

    con.close()
    # -------------------------------------
    con = connect()

    #test_tables(con)
    df = buscar_historico("PETR4.SA", "10y")
    if df is None:
        raise Exception("DF recebido é nulo")
    
    df = preparar_cotacoes(df, "PETR4.SA")
    print(df.head())
    print(df.dtypes)
    print(df.isna().sum())

    con.close()

def test_tables(con) -> None:
    print(con.execute("DESCRIBE dim_date").df())
    print("")
    print(con.execute("DESCRIBE daily_quotes").df())
    print("")
    print(con.execute("SHOW TABLES").df())
    print("")

    result = con.execute("""
        SELECT count(*), min(date), max(date) FROM dim_Date
    """).fetchone()
    print(f"{result}\n")

    result = con.execute("""
        SELECT * FROM dim_date LIMIT 7
    """).fetchone()
    print(f"{result}\n")

    result = con.execute("""
        SELECT * FROM dim_date ORDER BY data LIMIT 7
    """).fetchone()
    print(f"{result}\n")

def test_populate(con, inicio: str, fim: str) -> None:
    populate_dim_data(con, inicio, fim)

if __name__ == "__main__":  
    main()