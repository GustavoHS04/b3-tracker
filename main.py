from src.database.bootstrap_db import bootstrap_db
from src.database.queries import get_summary
from src.database.connect_db import connect
from src.summary import format_summary
from src.service import update_all, Status

import time
from src.logging_config import setup_logging
import logging


logger = logging.getLogger(__name__)

def update_database() -> None:
    with connect(read_only=False) as con:
        bootstrap_db(con)
        results = update_all(con)

        for ticker, status in results.items():
            if status is Status.UNAVAILABLE:
               print(f"Yahoo finance está atualmente indisponível para {ticker}.")
            elif status is Status.NOT_FOUND:
                print(f"O ticker '{ticker[:30]}' não foi encontrado.")
            elif status is Status.INVALID:
                print(f"O ticker '{ticker}' é inválido.")

def show_summary() -> None:
    with connect() as con:
        summary = get_summary(con)
        if summary.empty:
            print("Não há ativos cadastrados.")
        else:
            print(format_summary(summary).to_string(index=False))

def main() -> None:
    setup_logging()
    inicio = time.perf_counter()
    logger.info("Início da execução")

    try:
        update_database()
        show_summary()
    except Exception:
        logger.exception("Falha inesperada")
        raise
    finally:
        logger.info("Execução encerrada em %.1f s", time.perf_counter() - inicio)


if __name__ == "__main__":
    main()