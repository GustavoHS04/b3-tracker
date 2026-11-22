import logging
import asyncio
import pandas as pd
from telegram.ext import ContextTypes
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .locks import DB_LOCK
from ..config import TIMEZONE
from ..service import Status, update_all, get_summary
from .messages import build_summary_messages
from ..database.connect_db import connect
from ..database.bootstrap_db import ensure_db

logger = logging.getLogger(__name__)

def _closing_blocking() -> tuple[dict[str, Status], pd.DataFrame]:
    with connect(read_only=False) as con:
        ensure_db(con)
        results = update_all(con)
        summary = get_summary(con)

    return results, summary

def _has_bar_for(summary: pd.DataFrame, day: date) -> bool:
    if summary.empty:
        return False

    return bool((summary["date"].dt.date == day).any())

async def closing_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    if job is None or job.chat_id is None:
        logger.warning("Tarefa de fechamento sem chat_id")
        return

    async with DB_LOCK:
        results, summary = await asyncio.to_thread(_closing_blocking)

    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    if results and all(status is Status.UNAVAILABLE for status in results.values()):
        logger.warning("Todos resultados retornaram como indisponível")
        await context.bot.send_message(
            chat_id=job.chat_id,
            text="Não consegui atualizar os preços de hoje (fonte indisponível). O boletim não foi enviado."
        )
        return
    
    if not _has_bar_for(summary, today):
        logger.info("Sem barra de hoje; provavelmente sem pregão")
        return
    
    stale = [t for t, s in results.items() if s is not Status.OK]
    messages = build_summary_messages(summary, stale)
    for text in messages:
        await context.bot.send_message(chat_id=job.chat_id, text=text)

    logger.info("Boletim enviado: %d ativos em %d mensagem(ns)", len(summary), len(messages))
