import logging
import pandas as pd
from src import logger
from src.utils import get_tgt, save_df_to_db
from src.services import EpiasTransparencyerServices

@logger
def fetch_and_save_all_powerplants(service, tgt):
    response = service.info_powerplant_list(tgt)
    
    if response:
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            df = pd.DataFrame(items)
            save_df_to_db(df, table_name="powerplants_info", mode="replace")
            logging.info(f"Inserted {len(df)} powerplants into DuckDB table 'powerplants_info'.")

def main() -> None:
    tgt = get_tgt()
    if not tgt:
        logging.error("TGT not found. Please run tgt.py first.")
        return

    service = EpiasTransparencyerServices()
    fetch_and_save_all_powerplants(service, tgt)

if __name__ == "__main__":
    main()