from zoneinfo import ZoneInfo

from telegram.ext import Application, filters
import logging

from ..errors import ConfiguracaoError
from ..config import TIMEZONE, CLOSING_TIME, OPEN_FIRST_TRY
from .settings import require_telegram_config
from .jobs import closing_job, opening_job
from .handlers import registrar_handlers, publish_command

logger = logging.getLogger(__name__)

def build_application() -> Application:
    token, chat_id = require_telegram_config()
    try:
        owner_id = int(chat_id)
    except ValueError:
        raise ConfiguracaoError("TELEGRAM_CHAT_ID inválido: deve ser um número") from None

    async def _post_init(application: Application) -> None:
        await publish_command(application, owner_id)

    app = Application.builder().token(token).post_init(_post_init).build()
    only_owner = filters.Chat(chat_id=owner_id)
    registrar_handlers(app, only_owner)

    job_queue = app.job_queue
    if job_queue is None:
        raise ConfiguracaoError("JobQueue indisponível: instale python-telegram-bot[job-queue].")

    job_queue.run_daily(
        opening_job,
        time=OPEN_FIRST_TRY.replace(tzinfo=ZoneInfo(TIMEZONE)),
        days=(1,2,3,4,5),
        chat_id=owner_id,
        name="abertura"
    )

    job_queue.run_daily(
        closing_job,
        time=CLOSING_TIME.replace(tzinfo=ZoneInfo(TIMEZONE)),
        days=(1,2,3,4,5), # domigo = 0
        chat_id=owner_id,
        name="fechamento"
    )
    
    return app