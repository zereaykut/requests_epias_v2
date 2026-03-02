import logging
from src.utils import save_tgt
from src.services import EpiasTransparencyerServices

def main() -> None:
    logging.info("Attempting to fetch new TGT from EPIAS...")
    
    try:
        epias_service = EpiasTransparencyerServices()
        response = epias_service.tgt()
        
        if response.status_code in [200, 201]:
            tgt_token = response.text.strip()
            save_tgt(tgt_token)
            logging.info(f"TGT successfully updated in database. Status: {response.status_code}")
        else:
            logging.error(f"TGT fetch failed. Status: {response.status_code}, Detail: {response.text}")
            
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()