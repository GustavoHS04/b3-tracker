from pathlib import Path


# Define o path do banco de dados 
DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "b3.duckdb"

# Define as datas de início e fim para popular a dim_data (YYYY-MM-DD)
DATA_INICIO = "2016-01-01"
DATA_FIM    = "2035-12-31"

# Define o máximo de erros seguidos aceitáveis para adquirir tickers
# (Metodologia de verificação será alterada posteriormente)
MAX_FALHAS_SEGUIDAS = 3