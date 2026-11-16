import asyncio
from telegram import Bot
from src.config import TELEGRAM_TOKEN
from telegram.error import TelegramError

async def main() -> None:
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN não encontrado. Confira o .env")
        return

    try:
        async with Bot(TELEGRAM_TOKEN) as bot:  
            updates = await bot.get_updates()

    except TelegramError as e:
        print(f"Falha ao consultar o Telegram ({type(e).__name__})")
        return

    if not updates:
        print("Nenhuma mensagem encontrada. Mande /start ao seu bot e rode de novo.")
        return

    for update in reversed(updates):
        chat = update.effective_chat
        if chat is not None:
            print(f"chat_id: {chat.id} (tipo: {chat.type})")
            return

    print("Haviam atualizações, mas nenhuma com conversa associada. Mande /start de novo.")

if __name__ == "__main__":
    asyncio.run(main())