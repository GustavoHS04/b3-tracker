from telegram import Bot
from telegram.error import TelegramError

from ..errors import NotificacaoError
from .settings import require_telegram_config
async def send_message(text: str) -> None:
    token, chat_id = require_telegram_config()
    try:
        async with Bot(token) as bot:
            await bot.send_message(chat_id=chat_id, text=text)
    except TelegramError as e:
        raise NotificacaoError(f"Falha ao enviar mensagem ao Telegram ({type(e).__name__}).") from None