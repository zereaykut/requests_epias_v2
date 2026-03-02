import logging
import duckdb
import pandas as pd
from typing import Optional
from datetime import datetime

DB_PATH = "database.ddb"

def get_db_connection():
    """Returns a connection to the DuckDB database."""
    conn = duckdb.connect(DB_PATH)
    # Ensure TGT table exists
    conn.execute("CREATE TABLE IF NOT EXISTS tgt (ticket VARCHAR, updated_at TIMESTAMP)")
    return conn

def save_tgt(tgt_token: str) -> None:
    """Saves only the most recent TGT token by clearing the table first."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM tgt")
        conn.execute("INSERT INTO tgt VALUES (?, ?)", [tgt_token, datetime.now()])
    finally:
        conn.close()

def get_tgt() -> Optional[str]:
    """Retrieves the most recent TGT token from the database."""
    conn = get_db_connection()
    try:
        res = conn.execute("SELECT ticket FROM tgt ORDER BY updated_at DESC LIMIT 1").fetchone()
        return res[0] if res else None
    finally:
        conn.close()

def get_selected_powerplants():
    """Retrieves the list of selected powerplants to scrape."""
    conn = get_db_connection()
    try:
        # If you have populated a table named 'selected_powerplants'
        df = conn.execute("SELECT * FROM selected_powerplants").df()
        return df.to_dict(orient="records")
    except duckdb.CatalogException:
        logging.warning("Table 'selected_powerplants' does not exist. Using fallback data.")
        return [
            {
                "id": 1728,
                "name": "ÇANTA RES-40W000000007818V",
                "eic": "40W000000007818V",
                "shortName": "ÇANTA RES"
            }
        ]
    finally:
        conn.close()

def save_df_to_db(df: pd.DataFrame, table_name: str, mode: str = "append") -> None:
    """Saves a Pandas DataFrame to a DuckDB table."""
    if df.empty:
        return
        
    conn = get_db_connection()
    try:
        if mode == "replace":
            # Overwrites the table completely
            conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        else:
            # Appends data, creates table if it doesn't exist yet
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df LIMIT 0")
            conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
    finally:
        conn.close()