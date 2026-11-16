from telegram import Bot
from telegram.error import TelegramError

from ..config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from ..errors import NotificacaoError, ConfiguracaoError

async def send_message(text: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise ConfiguracaoError("Configurações de ambiente ausentes.")
    try:
        async with Bot(TELEGRAM_TOKEN) as bot:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    except TelegramError as e:
        raise NotificacaoError(f"Falha ao enviar mensagem ao Telegram ({type(e).__name__}).") from None