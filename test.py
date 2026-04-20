import logging
import pandas as pd
from datetime import date, timedelta
import time
from src import logger
from src.utils import save_tgt, get_tgt, save_df_to_db, get_data, get_powerplants_info
from src.services import EpiasTransparencyerServices

@logger
def fetch_and_save_info(service, tgt, fetch_func, table_name, mode="replace", **kwargs):
    """
    Generic helper to fetch info data and save to duckdb.
    Passes any extra **kwargs (like start_date and end_date) directly to the API function.
    """
    response = fetch_func(tgt, **kwargs)

    if response:
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            df = pd.DataFrame(items)

            if "organization_id" in kwargs:
                df["organization_id"] = kwargs["organization_id"]
            
            if "powerplant_id" in kwargs:
                df["powerplant_id"] = kwargs["powerplant_id"]

            save_df_to_db(df, table_name=table_name, mode=mode)
            logging.info(f"Inserted {len(df)} records into DuckDB table '{table_name}'.")
        else:
            logging.info(f"No data returned for table: {table_name}")

def main() -> None:
    # ----- Main Service -----
    service = EpiasTransparencyerServices()

    # ----- TGT -----
    response = service.tgt()
    
    if response.status_code in [200, 201]:
        tgt_token = response.text.strip()
        save_tgt(tgt_token)
        logging.info(f"TGT successfully updated in database. Status: {response.status_code}")
    else:
        logging.error(f"TGT fetch failed. Status: {response.status_code}, Detail: {response.text}")

    tgt = get_tgt()
    if not tgt:
        logging.error("TGT not found. Please run tgt.py first.")
        return
    
    # ----- Powerplant Info -----
    logging.info("Starting Data Retrieval for Powerplant Info")
    
    # time_format = "2026-02-01T00:00:00+03:00"
    start_date = str(date.today() - timedelta(days=30))
    end_date = str(date.today() - timedelta(days=1))
    period = str(date.today() - timedelta(days=3))
    logging.info(f"Fetching Consumer Count Data from {start_date} to {end_date}")

    fetch_and_save_info(service, tgt, service.info_powerplant_list, "info_powerplant_list", mode="replace")    
    fetch_and_save_info(service, tgt, service.info_organization_list, "info_organization_list", mode="replace", start_date=f"{start_date}T00:00:00+03:00", end_date=f"{end_date}T00:00:00+03:00")
   
    df_org = get_data("info_organization_list")
    for index, data in df_org.iterrows():
        fetch_and_save_info(service, tgt, service.info_uevcb_list, "info_uevcb_list", mode="append", organization_id=data.loc["organizationId"], start_date=f"{period}T00:00:00+03:00")
        fetch_and_save_info(service, tgt, service.info_powerplant_list_by_organization_id, "info_powerplant_list_by_organization_id", mode="append", start_date=f"{period}T00:00:00+03:00", end_date=f"{period}T00:00:00+03:00", organization_id=data.loc["organizationId"])
        time.sleep(3)

    # -------- Not Necessary --------
    # df_pp = get_data("info_powerplant_list")
    # for index, data in df_pp.iterrows():
    #     fetch_and_save_info(service, tgt, service.info_uevcb_list_by_powerplant_id, "info_uevcb_list_by_powerplant_id", mode="append", powerplant_id=data.loc["id"], start_date=f"{period}T00:00:00+03:00")
    #     time.sleep(2)

    # fetch_and_save_info(service, tgt, service.info_entso_x_codes, "info_entso_x_codes", mode="replace", period=f"{period}T00:00:00+03:00")
    # fetch_and_save_info(service, tgt, service.info_entso_w_uevcb, "info_entso_w_uevcb", mode="replace", period=f"{period}T00:00:00+03:00")
    # fetch_and_save_info(service, tgt, service.info_entso_w_organization, "info_entso_w_organization", mode="replace", period=f"{period}T00:00:00+03:00")
    # -------------------------------

    time.sleep(5)

    # ----- Powerplant Generation -----
    logging.info("Starting Data Retrieval for Powerplant Generation")

    # start_date = str(date.today() - timedelta(days=7))
    # end_date = str(date.today() - timedelta(days=1))
    start_date = "2026-01-01T00:00:00+03:00"
    end_date = "2026-02-28T23:00:00+03:00"
    logging.info(f"Data Collection Range: {start_date} to {end_date}")

    df_info = get_powerplants_info()

    df_info["genType"] = "not specified"
    gen_lower = df_info["realtimeGenerationName"].str.lower()
    df_info.loc[gen_lower.str.contains("gunes|günes|guneş|güneş|ges", na=False), "genType"] = "SPP"
    df_info.loc[gen_lower.str.contains("ruzgar|rüzgar|res", na=False), "genType"] = "WPP"
    df_info.loc[gen_lower.str.contains("dgkçs|dgkcs", na=False), "genType"] = "DGKCS"
    df_info.loc[gen_lower.str.contains("biyokütle|biyokutle|biyogaz", na=False), "genType"] = "BiyoKutle"

    df_info.to_csv("df_info.csv", index=True)
    
    # gen_type = "WPP"
    gen_type = "SPP"

    df_info = df_info[df_info["genType"]==gen_type]

    # Realtime Generation by Powerplants
    df_realtime_gen_info = df_info.dropna(subset=["realtimeGenerationId"]).drop_duplicates(subset=["realtimeGenerationId"])
    logging.info(f"Realtime Generation by Powerplants Info Data length: {len(df_realtime_gen_info)}")

    for index, row in df_realtime_gen_info.iterrows():
        response = service.realtime_generation(tgt, start_date, end_date, row.loc["realtimeGenerationId"])
        if response:
            data = response.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            
            if items:
                df = pd.DataFrame(items)

                df["realtimeGenerationId"] = row.loc["realtimeGenerationId"]
                df["organizationId"] = row.loc["organizationId"]
                df["powerPlantId"] = row.loc["powerPlantId"]
                df["uevcbId"] = row.loc["uevcbId"]
                df["powerPlantName"] = row.loc["powerPlantName"]

                save_df_to_db(df, table_name="powerplants_realtime_generation", mode="append")
                df.to_csv(f"""data_realtime_generation/{row.loc["realtimeGenerationId"]}.csv""", index=False)
                logging.info(f"""Realtime Generation Completed for: {row.loc["powerPlantName"]}""")
        time.sleep(3)
    logging.info("Realtime Generation by Powerplants Completed")

    time.sleep(5)

    # SBFGP(KUDUP) by Powerplants
    df_org_info = df_info.dropna(subset=["uevcbId"]).dropna(subset=["organizationId"]).drop_duplicates(subset=["uevcbId"])
    logging.info(f"SBFGP(KUDUP) by Powerplants Info Data length: {len(df_org_info)}")
    
    for index, row in df_org_info.iterrows():
        response = service.sbfgp(tgt, start_date, end_date, row.loc["organizationId"], row.loc["uevcbId"])
        if response:
            data = response.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            
            if items:
                df = pd.DataFrame(items)
                
                df["realtimeGenerationId"] = row.loc["realtimeGenerationId"]
                df["organizationId"] = row.loc["organizationId"]
                df["powerPlantId"] = row.loc["powerPlantId"]
                df["uevcbId"] = row.loc["uevcbId"]
                df["powerPlantName"] = row.loc["powerPlantName"]

                save_df_to_db(df, table_name="powerplants_sbfgp", mode="append")
                df.to_csv(f"""data_kudup/{row.loc["uevcbId"]}.csv""", index=False)
                logging.info(f"""SBFGP(KUDUP) Completed for: {row.loc["powerPlantName"]}""")
        time.sleep(3)
    logging.info("SBFGP(KUDUP) by Powerplants Completed")

    time.sleep(5)

    # ----- Price -----
    logging.info("Starting Data Retrieval for Price")

    # DAM MCP
    response = service.dam_mcp(tgt, start_date, end_date)
    if response:
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            df = pd.DataFrame(items)

            save_df_to_db(df, table_name="dam_mcp", mode="replace")


    # System Marginal Price
    response = service.system_marginal_price(tgt, start_date, end_date)
    if response:
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            df = pd.DataFrame(items)

            save_df_to_db(df, table_name="system_marginal_price", mode="replace")
    
    # Order Summary Up
    response = service.order_summary_up(tgt, start_date, end_date)
    if response:
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            df = pd.DataFrame(items)

            save_df_to_db(df, table_name="order_summary_up", mode="replace")

    # Order Summary Down
    response = service.order_summary_down(tgt, start_date, end_date)
    if response:
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            df = pd.DataFrame(items)

            save_df_to_db(df, table_name="order_summary_down", mode="replace")


if __name__ == "__main__":
    main()