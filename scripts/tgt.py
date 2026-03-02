# -*- coding: utf-8 -*-
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import save_json
from src.services import EpiasTransparencyerServices

def main() -> None:
    logging.info("Attempting to fetch new TGT from EPIAS...")
    
    try:
        # 1. Instantiate the service class first
        epias_service = EpiasTransparencyerServices()
        
        # 2. Call the method on the instance
        response = epias_service.tgt()
        
        if response.status_code in [200, 201]:
            # The TGT is usually returned as plain text from the CAS endpoint
            tgt_token = response.text.strip()
            
            # Save it as a JSON dictionary so your other scripts can read it easily
            tgt_data = {"TGT": tgt_token}
            
            os.makedirs("data", exist_ok=True)
            save_json(tgt_data, "data/tgt.json")
            
            logging.info(f"TGT successfully updated. Status: {response.status_code}")
        else:
            logging.error(f"TGT fetch failed. Status: {response.status_code}, Detail: {response.text}")
            
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Add a basic logging config if you haven't already to see the outputs in your console
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()