import pandas as pd

from ..config import DIAS_UTEIS_ANO, TELEGRAM_MAX_CHARS
from ..service import Status

EMOJI_TITLE = "\N{BAR CHART}"
EMOJI_TICKER = "\N{SMALL BLUE DIAMOND}"
EMOJI_UP = "\N{CHART WITH UPWARDS TREND}"
EMOJI_DOWN = "\N{CHART WITH DOWNWARDS TREND}"
EMOJI_FLAT = "\N{HEAVY MINUS SIGN}"

STATUS_TEXT = {
    Status.OK: "Ticker cadastrado com sucesso!",
    Status.EXISTS: "Ticker já está na lista de cadastros.",
    Status.NOT_FOUND: "Ticker não encontrado.",
    Status.UNAVAILABLE: "Fonte indisponível, tente novamente mais tarde.",
    Status.INVALID: "Formato inválido."
}

def _tg_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2

def _pct(value: float, signed: bool = False) -> str:
    if pd.isna(value):
        return "-"
    
    text = f"{value:+.2%}" if signed else f"{value:.2%}"
    return text.replace(".", ",")

def _money(value: float) -> str:
    if pd.isna(value):
        return "-"

    return f"R${value:.2f}".replace(".", ",")

def _trend_emoji(value: float) -> str:
    if pd.isna(value) or value == 0:
        return EMOJI_FLAT
    return EMOJI_UP if value > 0 else EMOJI_DOWN

def build_summary_blocks(df: pd.DataFrame) -> list[str]:
    blocks = [f"{EMOJI_TITLE} Resumo dos ativos"]

    for row in df.to_dict("records"):
        emoji = _trend_emoji(row["daily_return"])
        ticker = row["ticker"].removesuffix(".SA")
        date = row["date"].strftime("%d/%m/%Y")
        fechamento = _money(row["close"])
        daily_return = _pct(row["daily_return"], signed=True)
        media_movel = _money(row["moving_avg"])
        volatility_ann = _pct(row["volatility"] * DIAS_UTEIS_ANO ** 0.5)
        drawdown = _pct(row["drawdown"])

        blocks.append(
            f"{EMOJI_TICKER} {ticker} ({date})\n"
            f"{emoji} Fechamento: {fechamento} ({daily_return})\n"
            f"Média móvel: {media_movel}\n"
            f"Volatil. anual: {volatility_ann}\n"
            f"Drawdown: {drawdown}"
        )

    return blocks

def build_summary_messages(df: pd.DataFrame) -> list[str]:
    return split_message(build_summary_blocks(df), TELEGRAM_MAX_CHARS)

def split_message(blocks: list[str], limit: int) -> list[str]:
    messages = []
    current = ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if _tg_len(block) > limit:
            raise ValueError(f"Bloco de {_tg_len(block)} caracteres excede o limite de {limit}.")

        candidate = f"{current}\n\n{block}" if current else block
        if _tg_len(candidate) <= limit:
            current = candidate
        else:
            messages.append(current)
            current = block

    if current:
        messages.append(current)

    return messages

def format_add_results(results: dict[str, Status]) -> str:
    lines = []
    for key, status in results.items():
        label = key.removesuffix(".SA")[:30]
        lines.append(f"{label}: {STATUS_TEXT[status]}")

    return "\n".join(lines)