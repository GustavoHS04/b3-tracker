import logging
import sys

from src.logging_config import setup_logging
from src.bot.app import build_application
from src.errors import ConfiguracaoError

logger = logging.getLogger(__name__)

def main() -> int:
    setup_logging()
    try:
        app = build_application()
    except ConfiguracaoError as e:
        logger.error("%s", e)
        return 1
    
    app.run_polling()
    return 0

if __name__ == "__main__":
    sys.exit(main())