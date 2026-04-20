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

def get_data(table_name: str) -> pd.DataFrame:
    """Retrieve data fro given table name"""
    conn = get_db_connection()
    df = conn.execute(f"SELECT * FROM {table_name}").df()
    conn.close()
    return df

def get_powerplants_info():
    """Retrieves the dataframe for the info about powerplants to scrape."""
    conn = get_db_connection()
    try:
        df_info_powerplant_list = conn.execute(f"SELECT * FROM info_powerplant_list").df()
        df_info_organization_list = conn.execute(f"SELECT * FROM info_organization_list").df()
        df_info_uevcb_list = conn.execute(f"SELECT * FROM info_uevcb_list").df()
        df_info_powerplant_list_by_organization_id = conn.execute(f"SELECT * FROM info_powerplant_list_by_organization_id").df()

        df_info_powerplant_list = df_info_powerplant_list.rename(columns={
            "id": "realtimeGenerationId",
            "name": "realtimeGenerationName",
            "shortName": "realtimeGenerationShortName",
            "eic": "powerPlantEic"
        })

        df_info_uevcb_list = df_info_uevcb_list.rename(columns={
            "id": "uevcbId",
            "name": "uevcbName",
            "eic": "uevcbEic",
            "organization_id": "organizationId"
        })

        df_info_powerplant_list_by_organization_id = df_info_powerplant_list_by_organization_id.rename(columns={
            "id": "powerPlantId",
            "name": "powerPlantName",
            "eic": "powerPlantEic",
            "organization_id": "organizationId"
        }).drop(columns=["shortName"])

        df1 = pd.merge(df_info_organization_list, df_info_uevcb_list, on=["organizationId"], how="outer")
        df2 = pd.merge(df_info_powerplant_list_by_organization_id, df_info_powerplant_list, on=["powerPlantEic"], how="outer")
        df = pd.merge(df1, df2, on=["organizationId"], how="outer")
        return df
    except duckdb.CatalogException:
        logging.warning("Table 'selected_powerplants' does not exist. Using fallback data.")
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