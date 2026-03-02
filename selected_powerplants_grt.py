import logging
import pandas as pd
from datetime import date, timedelta
from src import logger
from src.utils import get_selected_powerplants, get_tgt, save_df_to_db
from src.services import EpiasTransparencyerServices

@logger
def fetch_and_save_grt(service, tgt, start, end, pp_info):
    grt_id = pp_info.get("id")
    name = pp_info.get("name")
    
    if grt_id is None:
        logging.warning(f"Skipping: grt_id is missing for {name}")
        return

    response = service.grt(tgt, start, end, grt_id)
    
    if response:
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            df = pd.DataFrame(items)
            df['grt_id'] = grt_id
            df['powerplant_name'] = name
            df['fetch_start'] = start
            df['fetch_end'] = end
            
            save_df_to_db(df, table_name="powerplants_grt_data", mode="append")
            logging.info(f"Appended {len(df)} rows to database for: {name}")
        else:
            logging.info(f"No GRT data returned from EPIAS for: {name}")

def main() -> None:
    start_date = str(date.today() - timedelta(days=7))
    end_date = str(date.today() - timedelta(days=1))
    logging.info(f"Data Collection Range: {start_date} to {end_date}")

    tgt = get_tgt()
    if not tgt:
        logging.error("No TGT found. Run tgt.py first.")
        return

    service = EpiasTransparencyerServices()
    pps_list = get_selected_powerplants()
    
    for pp in pps_list:
        fetch_and_save_grt(service, tgt, start_date, end_date, pp)

if __name__ == "__main__":
    main()