from pathlib import Path


# Define o path do banco de dados 
DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "b3.duckdb"

# Define as datas de início e fim para popular a dim_date (YYYY-MM-DD)
DATA_INICIO = "2016-01-01"
DATA_FIM    = "2035-12-31"

# Define o máximo de erros seguidos aceitáveis para adquirir tickers
# (Metodologia de verificação será alterada posteriormente)
MAX_FALHAS_SEGUIDAS = 3

# Define a quantidade de caracteres em um ticker determinado como válido
TICKER_MIN_LEN = 4
TICKER_MAX_LEN = 8

# Logging configs
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "b3_tracker.log"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUPS = 5