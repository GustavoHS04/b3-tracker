from src.database.bootstrap_db import bootstrap_db
from src.database.queries import get_summary
from src.database.connect_db import connect
from src.summary import format_summary
from src.service import update_all

def update_database() -> None:
    con = connect(read_only=False)

    bootstrap_db(con)
    results = update_all(con)

    for ticker in results:
        if results[ticker] is False:
            print(f"Não foi possível atualizar {ticker}.")

    con.close()

def show_summary() -> None:
    con = connect()

    summary = get_summary(con)
    if summary.empty:
        print("Não há ativos cadastrados na sua sessão.")
    else:
        print(format_summary(summary).to_string(index=False))

    con.close()

def main() -> None:
    update_database()
    show_summary()


if __name__ == "__main__":
    main()