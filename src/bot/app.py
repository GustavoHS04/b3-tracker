from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters
import logging
import asyncio

from ..database.connect_db import connect
from ..database.bootstrap_db import ensure_db
from ..service import add_tickers, Status
from ..errors import ConfiguracaoError, LimiteExcedidoError
from ..config import MAX_TICKERS_POR_VEZ
from .settings import require_telegram_config
from .messages import format_add_results

logger = logging.getLogger(__name__)

def _add_blocking(raws: list[str]) -> dict[str, Status]:
    with connect(read_only=False) as con:
        ensure_db(con)
        return add_tickers(con, raws)

async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Erro no bot", exc_info=context.error)
    if isinstance(update, Update):
        await _reply(update, "Algo deu errado. Tente de novo em instantes.")

async def _reply(update: Update, text: str) -> None:
    message = update.effective_message
    if message is None:
        logger.warning("Atualização sem mensagem; resposta descartada")
        return
    
    await message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, "Olá! Eu sou o InvestiBot, eu te ajudo a manter controle dos seus ativos.")


def build_application() -> Application:
    token, chat_id = require_telegram_config()
    try:
        owner_id = int(chat_id)
    except ValueError:
        raise ConfiguracaoError("TELEGRAM_CHAT_ID inválido: deve ser um número") from None

    app = Application.builder().token(token).build()
    only_owner = filters.Chat(chat_id=owner_id)
    app.add_handler(CommandHandler("start", start, filters=only_owner))
    app.add_handler(CommandHandler("add", add, filters=only_owner))
    app.add_error_handler(_on_error)

    return app

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    raws = " ".join(args).replace(",", " ").split()
    if not raws:
        await _reply(update, "Use: /add petr4 vale3")
        return

    await _reply(update, "Cadastrando, pode demorar um pouco...")
    try:
        results = await asyncio.to_thread(_add_blocking, raws)

    except LimiteExcedidoError:
        await _reply(update, f"Mande até {MAX_TICKERS_POR_VEZ} tickers por vez.")
        return

    await _reply(update, format_add_results(results))