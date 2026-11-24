import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import time
import logging

# Carregamento do env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Configurações do banco de dados
DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "b3.duckdb"

# Configurações de população do banco de dados
DATA_INICIO = "2016-01-01"
DATA_FIM    = "2035-12-31"

# Configurações dos tratamentos de erros
# (Metodologia de verificação será alterada posteriormente)
MAX_FALHAS_SEGUIDAS = 3
TICKER_MIN_LEN = 4
TICKER_MAX_LEN = 8
MAX_TICKERS_POR_VEZ = 10
YF_RETRIES = 2
NAME_MAX_LEN = 40
LOCK_TIMEOUT_SECONDS = 300

# Configurações de logging
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "b3_tracker.log"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUPS = 5
LIB_LOG_LEVELS = {
    "yfinance": logging.WARNING,
    "peewee": logging.WARNING,
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "telegram": logging.INFO,
    "asyncio": logging.WARNING,
    "apscheduler": logging.INFO,
}

# Configurações do Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_TIMEOUT = 15
TELEGRAM_MAX_CHARS = 4000

# Configurações dos ativos
DIAS_UTEIS_ANO = 252 # Utilizado para cálculos de anualização
TIMEZONE = "America/Sao_Paulo"
CLOSING_TIME = time(18, 30)
OPEN_FIRST_TRY = time(10, 22)
OPEN_GIVE_UP = time(10, 50)
OPEN_RETRY_SECONDS = 120