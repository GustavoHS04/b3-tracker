from pathlib import Path
import logging

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

# Configurações de logging
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "b3_tracker.log"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUPS = 5
NOISY_LOGGERS = ("peewee", "yfinance")
LIBS_LOG_LEVEL = logging.WARNING