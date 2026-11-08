from duckdb import DuckDBPyConnection

from ..config import DATA_INICIO, DATA_FIM
from .create_db import create
from .populate_db import populate_dim_data

def bootstrap_db(con: DuckDBPyConnection) -> None:
    create(con)

    populate_dim_data(con, DATA_INICIO, DATA_FIM)