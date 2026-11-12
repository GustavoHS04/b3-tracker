from src.database.bootstrap_db import bootstrap_db
from src.database.queries import get_summary
from src.database.connect_db import connect
from src.summary import format_summary
from src.service import update_all, Status

def update_database() -> None:
    with connect(read_only=False) as con:
        bootstrap_db(con)
        results = update_all(con)

        for ticker, status in results.items():
            if status is not Status.OK:
                if status is Status.UNAVAILABLE:
                   print(f"Yahoo finance está atualmente indisponível para {ticker}.")
                if status is Status.NOT_FOUND:
                    print(f"O ticker '{ticker}' não foi encontrado.")

def show_summary() -> None:
    with connect() as con:
        summary = get_summary(con)
        if summary.empty:
            print("Não há ativos cadastrados.")
        else:
            print(format_summary(summary).to_string(index=False))

def main() -> None:
    update_database()
    show_summary()


if __name__ == "__main__":
    main()