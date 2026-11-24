import logging
import asyncio
import pandas as pd
from telegram.ext import ContextTypes
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .locks import DB_LOCK
from .messages import build_summary_messages, build_open_message
from ..errors import TickerNaoEncontradoError, FonteIndisponivelError
from ..sources.yahoo import parse_open
from ..config import TIMEZONE, OPEN_GIVE_UP, OPEN_RETRY_SECONDS
from ..service import Status, update_all, get_summary, buscar_historico
from ..database.queries import list_tickers
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

def _list_tickers_blocking() -> list[str]:
    with connect(read_only=False) as con:
        return list_tickers(con)

def _fetch_open(ticker: str, today: date):
    try:
        return parse_open(buscar_historico(ticker, periodo="5d"), today)
    except (TickerNaoEncontradoError, FonteIndisponivelError):
        return None

def _collect_opens(tickers: list[str], today: date):
    rows, pending = [], []
    for ticker in tickers:
        result = _fetch_open(ticker, today)
        if result is None:
            pending.append(ticker)
        else:
            rows.append((ticker, *result))

    return rows, pending

def _chat_id_or_warn(context: ContextTypes.DEFAULT_TYPE, task: str) -> int | str | None:
    job = context.job
    if job is None or job.chat_id is None:
        logger.warning("Tarefa de %s sem chat_id", task)
        return None
    return job.chat_id

async def opening_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id_or_warn(context, task="abertura")
    if chat_id is None:
        return

    async with DB_LOCK:
        tickers = await asyncio.to_thread(_list_tickers_blocking)
    if not tickers:
        logger.info("Sem ativos na abertura de hoje")
        return

    tz = ZoneInfo(TIMEZONE)
    today = datetime.now(tz).date()
    deadline = datetime.combine(today, OPEN_GIVE_UP, tzinfo=tz)

    while True:
        if await asyncio.to_thread(_fetch_open, tickers[0], today) is not None:
            break
        if datetime.now(tz) >= deadline:
            logger.info("Sem abertura válida; provavelmente sem pregão")
            return
        await asyncio.sleep(OPEN_RETRY_SECONDS)

    rows, pending = await asyncio.to_thread(_collect_opens, tickers, today)
    message = build_open_message(rows, pending, today)

    await context.bot.send_message(chat_id, text=message)
    logger.info("Abertura enviada: %d ativos (%d sem dados)", len(rows), len(pending))

async def closing_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id_or_warn(context, task="fechamento")
    if chat_id is None:
        return

    async with DB_LOCK:
        results, summary = await asyncio.to_thread(_closing_blocking)

    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    if results and all(status is Status.UNAVAILABLE for status in results.values()):
        logger.warning("Todos resultados retornaram como indisponível")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Não consegui atualizar os preços de hoje (fonte indisponível). O boletim não foi enviado."
        )
        return
    
    if not _has_bar_for(summary, today):
        logger.info("Sem barra de hoje; provavelmente sem pregão")
        return
    
    stale = [t for t, s in results.items() if s is not Status.OK]
    messages = build_summary_messages(summary, stale)
    for text in messages:
        await context.bot.send_message(chat_id=chat_id, text=text)

    logger.info("Boletim enviado: %d ativos em %d mensagem(ns)", len(summary), len(messages))
