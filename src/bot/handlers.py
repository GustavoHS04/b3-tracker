from telegram import Update, BotCommand, BotCommandScopeChat
from telegram.ext import ContextTypes, Application, CommandHandler
from telegram.error import TelegramError
import pandas as pd
import logging
import asyncio

from ..database.connect_db import connect
from ..database.bootstrap_db import ensure_db
from ..database.queries import list_tickers_with_names
from ..service import Status, add_tickers, remove_tickers, parse_ticker, get_summary
from ..errors import LimiteExcedidoError
from ..config import MAX_TICKERS_POR_VEZ, NAME_MAX_LEN, TELEGRAM_MAX_CHARS, LOCK_TIMEOUT_SECONDS
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

async def _reply(update: Update, text: str) -> None:
    message = update.effective_message
    if message is None:
        logger.warning("Atualização sem mensagem; resposta descartada")
        return
    
    await message.reply_text(text)


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"

def _add_blocking(raws: list[str]) -> dict[str, Status]:
    with connect(read_only=False) as con:
        ensure_db(con)
        return add_tickers(con, raws)

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

def _help_text() -> str:
    lines = ["Comandos:"]
    for name, (_, description) in _COMMANDS.items():
        lines.append(f"/{name} - {description}")

    return "\n".join(lines)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, "Olá! Eu sou o InvestiBot, eu te ajudo a manter controle dos seus ativos.\n\n" + _help_text())

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, _help_text())

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    raws = " ".join(args).replace(",", " ").split()
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
    args = context.args or []
    raws = " ".join(args).replace(",", " ").split()
    if not raws:
        await _reply(update, "Use: /remover petr4 val3")
        return
    try:
        results = await _run_db(_remove_blocking, raws)
    except LimiteExcedidoError:
        await _reply(update, f"Mande atẽ {MAX_TICKERS_POR_VEZ} tickers por vez.")
        return
    await _reply(update, format_results(results, REMOVE_TEXT))
    
async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pairs = await _run_db(_list_blocking)
    if not pairs:
        await _reply(update, "Nenhum ativo cadastrado. Use /add petr4 vale3")
        return

    lines = [f"Ativos cadastrados ({len(pairs)}):"]
    for ticker, name in pairs:
        label = ticker.removesuffix(".SA")
        lines.append(label if name == ticker else f"{label}: {_short(name, NAME_MAX_LEN)}")

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
    raws = context.args or []
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

    
_COMMANDS = {
    "start": (start, "Boas-vindas e lista de comandos"),
    "help": (help, "Lista os comandos"),
    "add": (add, "Adiciona tickers (ex.: /add petr4 vale3)"),
    "remover": (remover, "Remove tickers (ex.: /remover petr4 vale3)"),
    "lista": (lista, "Mostra os ativos cadastrados"),
    "resumo": (resumo, "Resumo dos ativos (último fechamento)"),
    "ativo": (ativo, "Resumo de um ativo (ex.: /ativo petr4)")
}

def registrar_handlers(app: Application, only_owner) -> None:
    for name, (callback, _) in _COMMANDS.items():
        app.add_handler(CommandHandler(name, callback, filters=only_owner))
    app.add_error_handler(_on_error)

async def publish_command(app: Application, owner_id: int) -> None:
    commands = [BotCommand(name, description) for name, (_, description) in _COMMANDS.items()]
    try:
        await app.bot.set_my_commands(commands, scope=BotCommandScopeChat(owner_id))
    except TelegramError as e:
        logger.warning("Não consegui publicar o menu de comandos (%s)", type(e).__name__)