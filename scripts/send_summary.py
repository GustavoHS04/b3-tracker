import asyncio, logging, sys

from src.logging_config import setup_logging
from src.bot.client import send_message
from src.database.connect_db import connect
from src.database.queries import get_summary
from src.bot.messages import build_summary_blocks, split_message

from src.config import TELEGRAM_MAX_CHARS

from src.errors import NotificacaoError, ConfiguracaoError

logger = logging.getLogger(__name__)

async def _send_all(messages: list[str]) -> None:
    for text in messages:
        await send_message(text)

def main() -> int:
    setup_logging()
    with connect() as con:
        df = get_summary(con)
    if df.empty:
        logger.warning("Nenhum ativo cadastrado; nada a enviar")
        return 0

    messages = split_message(build_summary_blocks(df), TELEGRAM_MAX_CHARS)
    try:
        asyncio.run(_send_all(messages))
    except (NotificacaoError, ConfiguracaoError) as e:
        logger.error("%s", e)
        return 1

    logger.info("Resumo enviado: %d ativos em %d mensagem(ns)", len(df), len(messages))

    return 0

if __name__ == "__main__":
    sys.exit(main())