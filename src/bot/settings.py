from ..config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from ..errors import ConfiguracaoError

def require_telegram_config() -> tuple[str, str]:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        missing = [
            name
            for name, value in (
                ("TELEGRAM_TOKEN", TELEGRAM_TOKEN),
                ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
            )
            if not value
        ]

        raise ConfiguracaoError(f"Variáveis ausentes no .env: {', '.join(missing)}.")

    return TELEGRAM_TOKEN, TELEGRAM_CHAT_ID