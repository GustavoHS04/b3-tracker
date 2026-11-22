import logging
from datetime import date, datetime, time
from time import sleep
from zoneinfo import ZoneInfo

from src.config import TIMEZONE
from src.errors import FonteIndisponivelError, TickerNaoEncontradoError
from src.logging_config import setup_logging
from src.sources.yahoo import buscar_historico

logger = logging.getLogger(__name__)

TZ = ZoneInfo(TIMEZONE)
TICKERS = ["VALE3.SA", "ITUB4.SA"]
SAMPLE_TIMES = [time(10, 0, 30)] + [time(10, m) for m in range(10, 41)]

def _wait_until(target: datetime) -> None:
    delay = ((target - datetime.now(TZ))).total_seconds()
    if delay > 0:
        sleep(delay)
    else:
        logger.info("ESPERA horário %s já passou; medindo agora", target.strftime("%H:%M:%S"))

def _sample(ticker: str, today: date) -> None:
    now = datetime.now(TZ).strftime("%H:%M:%S")
    try:
        df = buscar_historico(ticker, inicio=today)
    except TickerNaoEncontradoError:
        logger.info("MEDIDA %s %s sem_barra", now, ticker)
        return
    except FonteIndisponivelError:
        logger.info("MEDIDA %s %s fonte_indisponivel", now, ticker)
        return

    last_date = df.index[-1].date()
    open = float(df["Open"].iloc[-1])
    volume = (df["Volume"].iloc[-1])
    close = float(df["Close"].iloc[-1])
    valid = last_date == today and open > 0
    logger.info(
        "MEDIDA %s %s valida=%s data=%s open=%.2f volume=%s close=%.2f",
        now, ticker, valid, last_date, open, volume, close,
    )

def main() -> None:
    setup_logging()
    today = datetime.now(TZ).date()
    logger.info("MEDIDA início: %s, %d horários, tickers %s", today, len(SAMPLE_TIMES), TICKERS)

    for target in SAMPLE_TIMES:
        _wait_until(datetime.combine(today, target, tzinfo=TZ))
        for ticker in TICKERS:
            _sample(ticker, today)

    logger.info("MEDIDA fim")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("MEDIDA interrompida")