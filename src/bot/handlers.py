from telegram import Update, BotCommand, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import TelegramError
import pandas as pd
import logging
import asyncio
import secrets
import time

from ..database.connect_db import connect
from ..database.bootstrap_db import ensure_db
from ..database.queries import list_tickers_with_names, get_summary
from ..service import Status, add_tickers, remove_tickers, parse_ticker, lookup_tickers
from ..errors import LimiteExcedidoError
from ..config import MAX_TICKERS_POR_VEZ, NAME_MAX_LEN, TELEGRAM_MAX_CHARS, LOCK_TIMEOUT_SECONDS, CONFIRM_TTL_SECONDS
from .locks import DB_LOCK
from .messages import ADD_TEXT, REMOVE_TEXT, format_results, split_message, build_summary_messages

logger = logging.getLogger(__name__)


async def _run_db(func, *args):
    logger.debug("Aguardando DB_LOCK para %s", func.__name__)
    await asyncio.wait_for(DB_LOCK.acquire(), timeout=LOCK_TIMEOUT_SECONDS)
    try:
        return await asyncio.to_thread(func, *args)
    finally:
        DB_LOCK.release()

async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Erro no bot", exc_info=context.error)
    if isinstance(update, Update):
        await _reply(update, "Algo deu errado. Tente de novo em instantes.")

async def _reply(update: Update, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    message = update.effective_message
    if message is None:
        logger.warning("Atualização sem mensagem; resposta descartada")
        return
    
    await message.reply_text(text, reply_markup=reply_markup)

def _tokens(text: str) -> list[str]:
    return text.replace(",", " ").split()

def _parse_args(context: ContextTypes.DEFAULT_TYPE) -> list[str]:
    return _tokens(" ".join(context.args or []))

def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"

def _label(ticker: str) -> str:
    return ticker.removesuffix(".SA")

def _ticker_line(ticker: str, name: str) -> str:
    if name == ticker:
        return _label(ticker)
    return f"{_label(ticker)}: {_short(name, NAME_MAX_LEN)}"
    
def _add_blocking(raws: list[str]) -> dict[str, Status]:
    with connect(read_only=False) as con:
        ensure_db(con)
        return add_tickers(con, raws)

def _add_summary_blocking(raws: list[str]) -> tuple[dict[str, Status], pd.DataFrame]:
    with connect(read_only=False) as con:
        ensure_db(con)
        results = add_tickers(con, raws)
        summary = get_summary(con)
    return results, summary

def _remove_blocking(raws: list[str]) -> dict[str, Status]:
    with connect(read_only=False) as con:
        ensure_db(con)
        return remove_tickers(con, raws)
     
def _list_blocking() -> list[tuple[str, str]]:
    with connect(read_only=False) as con:
        ensure_db(con)
        return list_tickers_with_names(con)

def _summary_blocking() -> pd.DataFrame:
    with connect(read_only=False) as con:
        ensure_db(con)
        return get_summary(con)

def _lookup_blocking(raws: list[str]):
    with connect(read_only=False) as con:
        ensure_db(con)
        results, names = lookup_tickers(con, raws)
        summary = get_summary(con)
    return results, names, summary

def _help_text() -> str:
    lines = ["Comandos:"]
    for name, (_, description) in _COMMANDS.items():
        lines.append(f"/{name} - {description}")
    lines.append("")
    lines.append("Ou mande só o ticker (ex.: petr4) para ver o resumo.")

    return "\n".join(lines)

def _new_pending(context: ContextTypes.DEFAULT_TYPE, tickers: list[str]) -> str | None:
    chat_data = context.chat_data
    if chat_data is None:
        return None

    pending = chat_data.setdefault("pending", {})
    now = time.monotonic()
    for key in [k for k, v in pending.items() if now - v["at"] > CONFIRM_TTL_SECONDS]:
        del pending[key]
    pending_id = secrets.token_hex(4)
    pending[pending_id] = {"tickers": tickers, "at": now}

    return pending_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, "Olá! Eu sou o InvestiBot, eu te ajudo a manter controle dos seus ativos.\n\n" + _help_text())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, _help_text())

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raws = _parse_args(context)

    if not raws:
        await _reply(update, "Use: /add petr4 vale3")
        return

    await _reply(update, "Cadastrando, pode demorar um pouco...")
    try:
        results = await _run_db(_add_blocking, raws)

    except LimiteExcedidoError:
        await _reply(update, f"Mande até {MAX_TICKERS_POR_VEZ} tickers por vez.")
        return

    await _reply(update, format_results(results, ADD_TEXT))

async def remover(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raws = _parse_args(context)

    if not raws:
        await _reply(update, "Use: /remover petr4 vale3")
        return
    try:
        results = await _run_db(_remove_blocking, raws)
    except LimiteExcedidoError:
        await _reply(update, f"Mande até {MAX_TICKERS_POR_VEZ} tickers por vez.")
        return
    await _reply(update, format_results(results, REMOVE_TEXT))
    
async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pairs = await _run_db(_list_blocking)
    if not pairs:
        await _reply(update, "Nenhum ativo cadastrado. Use /add petr4 vale3")
        return

    lines = [f"Ativos cadastrados ({len(pairs)}):"]
    for ticker, name in pairs:
        label = _label(ticker)
        lines.append(_ticker_line(ticker, name))

    for text in split_message(lines, TELEGRAM_MAX_CHARS, sep="\n"):
        await _reply(update, text)

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    df = await _run_db(_summary_blocking)
    if df.empty:
        await _reply(update, "Nenhum ativo com dados. Use /add petr4")
        return
    for text in build_summary_messages(df):
        await _reply(update, text)

async def ativo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raws = _parse_args(context)
    if len(raws) != 1:
        await _reply(update, "Use: /ativo petr4")
        return

    ticker = parse_ticker(raws[0])
    if ticker is None:
        await _reply(update, "Formato de ticker inválido.")
        return

    df = await _run_db(_summary_blocking)
    one = df[df["ticker"] == ticker]
    if one.empty:
        await _reply(update, f"Sem dados para {ticker.removesuffix('.SA')}. Cadastre com /add ou aguarde a próxima atualização.")
        return
    for text in build_summary_messages(one):
        await _reply(update, text)

async def ticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return

    raws = _tokens(message.text)
    if not raws:
        return
    
    if len(raws) > MAX_TICKERS_POR_VEZ or any(parse_ticker(r) is None for r in raws):
        await _reply(update, "Não entendi. Mande um ou mais tickers (ex.: petr4 vale3) ou use /help")
        return

    results, names, summary = await _run_db(_lookup_blocking, raws)

    existing = [t for t, s in results.items() if s is Status.EXISTS]
    found = [t for t, s in results.items() if s is Status.FOUND]
    others = {t: s for t, s in results.items() if s not in (Status.EXISTS, Status.FOUND)}

    shown = summary[summary["ticker"].isin(existing)]
    with_data = set(shown["ticker"])
    no_data = [t for t in existing if t not in with_data]

    if not shown.empty:
        for text in build_summary_messages(shown):
            await _reply(update, text)

    lines: list[str] = []
    keyboard = None
    if no_data:
        lines.append("Cadastrados, ainda sem dados: " + ", ".join(_label(t) for t in no_data))
    if found:
        lines.append("Encontrei, ainda não cadastrados:")
        lines.extend(_ticker_line(t, names[t]) for t in found)
        pending_id = _new_pending(context, found)
        if pending_id is not None:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Cadastrar", callback_data=f"add:{pending_id}"),
                InlineKeyboardButton("Cancelar", callback_data=f"no:{pending_id}"),
            ]])

    if others:
        lines.append(format_results(others, ADD_TEXT))

    if lines:
        await _reply(update, "\n".join(lines), reply_markup=keyboard)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, "Comando desconhecido. Use /help")

async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    chat = update.effective_chat
    owner_id = context.bot_data.get("owner_id")
    if owner_id is None:
        logger.error("owner_id ausente em bot_data; cliques ignorados (confira app.py)")
        return
    if chat is None or chat.id != context.bot_data.get("owner_id"):
        logger.warning("Clique em um chat não autorizado; ignorado")
        return
    
    action, _, pending_id = (query.data or "").partition(":")
    chat_data = context.chat_data
    item = chat_data.get("pending", {}).pop(pending_id, None) if chat_data is not None else None
    if item is None or time.monotonic() - item["at"] > CONFIRM_TTL_SECONDS:
        await query.edit_message_text("Essa confirmação expirou ou já foi usada.")
        return
    if action == "no":
        await query.edit_message_text("Cancelado.")
        return
    tickers = item["tickers"]
    
    await query.edit_message_text("Cadastrando, pode demorar um pouco...")
    results, summary = await _run_db(_add_summary_blocking, tickers)

    await _reply(update, format_results(results, ADD_TEXT))
    registered = [t for t, s in results.items() if s is Status.OK]
    shown = summary[summary["ticker"].isin(registered)]
    if not shown.empty:
        for text in build_summary_messages(shown):
            await _reply(update, text)

_COMMANDS = {
    "start": (start, "Boas-vindas e lista de comandos"),
    "help": (help_command, "Lista os comandos"),
    "add": (add, "Adiciona tickers (ex.: /add petr4 vale3)"),
    "remover": (remover, "Remove tickers (ex.: /remover petr4 vale3)"),
    "lista": (lista, "Mostra os ativos cadastrados"),
    "resumo": (resumo, "Resumo dos ativos (último fechamento)"),
    "ativo": (ativo, "Resumo de um ativo (ex.: /ativo petr4)")
}

def registrar_handlers(app: Application, only_owner) -> None:
    for name, (callback, _) in _COMMANDS.items():
        app.add_handler(CommandHandler(name, callback, filters=only_owner))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & only_owner, ticker_message))
    app.add_handler(MessageHandler(filters.COMMAND & only_owner, unknown))
    app.add_handler(CallbackQueryHandler(confirm_callback, pattern=r"^(add|no):[0-9a-f]{8}$"))
    app.add_error_handler(_on_error)

async def publish_command(app: Application, owner_id: int) -> None:
    commands = [BotCommand(name, description) for name, (_, description) in _COMMANDS.items()]
    try:
        await app.bot.set_my_commands(commands, scope=BotCommandScopeChat(owner_id))
    except TelegramError as e:
        logger.warning("Não consegui publicar o menu de comandos (%s)", type(e).__name__)