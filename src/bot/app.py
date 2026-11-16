from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters
import logging

from ..errors import ConfiguracaoError
from .settings import require_telegram_config

logger = logging.getLogger(__name__)

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

    return app