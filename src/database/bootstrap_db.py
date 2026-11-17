import logging
from duckdb import DuckDBPyConnection

from ..config import DATA_INICIO, DATA_FIM
from .create_db import create, REQUIRED_TABLES
from .populate_db import populate_dim_date

logger = logging.getLogger(__name__)

def is_database_ready(con: DuckDBPyConnection) -> bool:
    rows = con.execute("SHOW TABLES").fetchall()
    existing = {row[0] for row in rows}
    if not REQUIRED_TABLES <= existing:
        return False

    row = con.execute("SELECT COUNT(*) FROM dim_date").fetchone()
    
    return row is not None and row[0] > 0

def ensure_db(con: DuckDBPyConnection) -> None:
    if not is_database_ready(con):
        logger.warning("Banco incompleto ou ausente; recriando")
        bootstrap_db(con)

def bootstrap_db(con: DuckDBPyConnection) -> None:
    create(con)

    populate_dim_date(con, DATA_INICIO, DATA_FIM)