# -*- coding: utf-8 -*-
import os
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

class EpiasTransparencyerServices:
    def __init__(self):
        self.main_url = "https://seffaflik.epias.com.tr/electricity-service"
        
        # 1. Setup the Session
        self.session = requests.Session()
        
        # 2. Configure the Retry Strategy
        retry_strategy = Retry(
            total=3,                          # Total number of retries
            backoff_factor=1,                 # Wait 1s, 2s, 4s between attempts
            status_forcelist=[429, 500, 502, 503, 504], # Retry on these status codes
            allowed_methods=["POST", "GET"]   # EPIAS uses POST for data retrieval
        )
        
        # 3. Mount the adapter to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # 4. Standard Headers
        self.session.headers.update({
            "Accept-Language": "en",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _post(self, endpoint: str, tgt: str, payload: Dict[str, Any]) -> requests.Response:
        """Internal helper to send POST requests with TGT header."""
        url = f"{self.main_url}/{endpoint}"
        headers = {"TGT": tgt} if tgt else {}
        # Merge specific headers with session headers
        request_headers = self.session.headers.copy()
        request_headers.update(headers)
        
        return self.session.post(url, json=payload, headers=request_headers)

    def _format_dates(self, start_date: str, end_date: str) -> Dict[str, str]:
        """Internal helper to format date payload."""
        return {"startDate": start_date, "endDate": end_date}

    # ==========================================
    # AUTHENTICATION SERVICE
    # ==========================================

    def tgt(self) -> requests.Response:
        """Fetch the Ticket Granting Ticket (TGT) from EPIAS CAS."""
        # Note: Make sure EPIAS_USERNAME and EPIAS_PASSWORD are set in your .env file
        username = os.getenv("EPIAS_TRANSPARENCY_USERNAME")
        password = os.getenv("EPIAS_TRANSPARENCY_PASSWORD")
        
        cas_url = "https://giris.epias.com.tr/cas/v1/tickets"
        payload = {
            "username": username,
            "password": password
        }
        
        # CAS typically requires form-urlencoded data and returns plain text
        headers = {
            "Accept": "text/plain",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        return self.session.post(cas_url, data=payload, headers=headers)

    # ==========================================
    # 5. CONSUMPTION (TÜKETİM) SERVICES
    # ==========================================

    def eligible_consumer_count(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """5.1. Tüketici Sayısı Listeleme Servisi (Eligible Consumer Count)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/consumption/data/eligible-consumer-count", tgt, payload)

    def profile_group_list(self, tgt: str) -> requests.Response:
        """5.2. Profil Grubu Listeleme Servisi (Profile Group List)"""
        return self._post("v1/consumption/data/profile-group-list", tgt, {})

    def consumption_quantity(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """5.3. Tüketim Miktarları Listeleme Servisi (Realized Consumption)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/consumption/data/realized-consumption", tgt, payload)

    def demand_forecast(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """5.4. Talep Tahmini Listeleme Servisi (Load Estimation Plan)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/consumption/data/load-estimation-plan", tgt, payload)

    def distribution_regions(self, tgt: str) -> requests.Response:
        """5.5. Dağıtım Bölgesi Servisi (Distribution Regions)"""
        return self._post("v1/consumption/data/distribution-region-list", tgt, {})

    def eligible_consumer_quantity(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """5.7. Serbest Tüketici Tüketim Miktarı Listeleme Servisi (Eligible Consumer Quantity)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/consumption/data/eligible-consumer-quantity", tgt, payload)

    def real_time_consumption(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Gercek Zamanli Tuketim Servisi"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/consumption/data/realtime-consumption", tgt, payload)

    def ue_consumption(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """UE Tüketim Miktarı (Under Supply Consumption)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/consumption/data/ue-consumption", tgt, payload)

    # ==========================================
    # 6. PRODUCTION (ÜRETİM) SERVICES
    # ==========================================

    def info_powerplant_list(self, tgt: str) -> requests.Response:
        """Santral Listeleme Servisi (Powerplant List)"""
        return self._post("v1/production/data/powerplant-list", tgt, {})

    def installed_capacity(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Kurulu Güç Listeleme Servisi (Installed Capacity)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/production/data/installed-capacity", tgt, payload)

    def real_time_generation(self, tgt: str, start_date: str, end_date: str, powerplant_id: Union[int, None] = None) -> requests.Response:
        """Gercek Zamanli Uretim (GZUP) Servisi (Real Time Generation)"""
        payload = self._format_dates(start_date, end_date)
        if powerplant_id:
            payload["powerPlantId"] = powerplant_id
        return self._post("v1/production/data/real-time-generation", tgt, payload)

    def dpp(self, tgt: str, start_date: str, end_date: str, organization_id: Union[int, None] = None, powerplant_id: Union[int, None] = None) -> requests.Response:
        """KUDUP (DPP) Listeleme Servisi"""
        payload = self._format_dates(start_date, end_date)
        if organization_id:
            payload["organizationId"] = organization_id
        if powerplant_id:
            payload["powerPlantId"] = powerplant_id
        return self._post("v1/production/data/dpp", tgt, payload)

    def fdpp(self, tgt: str, start_date: str, end_date: str, organization_id: Union[int, None] = None, powerplant_id: Union[int, None] = None) -> requests.Response:
        """
        Kesinleşmiş Günlük Üretim Planı (KGÜP) - Final Daily Production Plan
        Endpoint: v1/production/data/final-daily-production-plan
        """
        payload = self._format_dates(start_date, end_date)
        if organization_id:
            payload["organizationId"] = organization_id
        if powerplant_id:
            payload["powerPlantId"] = powerplant_id
        return self._post("v1/production/data/final-daily-production-plan", tgt, payload)

    def aic(self, tgt: str, start_date: str, end_date: str, organization_id: Union[int, None] = None, powerplant_id: Union[int, None] = None) -> requests.Response:
        """
        Emre Amade Kapasite (EAK) - Available Capacity
        Endpoint: v1/production/data/aic
        Note: EAK often corresponds to 'aic' (Available Installed Capacity) in EPIAS services.
        If 'aic' was already defined as 'sfy_capacity', this is an alias or the specific EAK endpoint.
        """
        payload = self._format_dates(start_date, end_date)
        if organization_id:
            payload["organizationId"] = organization_id
        if powerplant_id:
            payload["powerPlantId"] = powerplant_id
        return self._post("v1/production/data/aic", tgt, payload)

    def initial_fdpp(self, tgt: str, start_date: str, end_date: str, organization_id: Union[int, None] = None, powerplant_id: Union[int, None] = None) -> requests.Response:
        """
        İlk KGÜP - Initial Daily Production Plan
        Endpoint: v1/production/data/initial-daily-production-plan
        """
        payload = self._format_dates(start_date, end_date)
        if organization_id:
            payload["organizationId"] = organization_id
        if powerplant_id:
            payload["powerPlantId"] = powerplant_id
        return self._post("v1/production/data/initial-daily-production-plan", tgt, payload)

    def fault_maintenance(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Arıza Bakım Bildirimleri (Fault-Maintenance)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/production/data/fault-maintenance", tgt, payload)

    # ==========================================
    # 7. MARKET (PİYASALAR) SERVICES
    # ==========================================

    # --- DAM (GÖP) ---
    def mcp(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """PTF Listeleme Servisi (MCP - Market Clearing Price)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/dam/data/mcp", tgt, payload)

    def dam_volume(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """GÖP Eşleşme Miktarı (DAM Trade Volume)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/dam/data/amount-of-cleared-from-match", tgt, payload)

    def dam_bid_offer(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """GÖP Teklif Edilen Alış/Satış Miktarları"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/dam/data/submitted-bid-offer-volume", tgt, payload)

    # --- IDM (GİP) ---
    def idm_matching_quantity(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """GİP Eşleşme Miktarı Listeleme Servisi"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/idm/data/matching-quantity", tgt, payload)

    def idm_summary(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """GİP Özet Verileri (IDM Summary)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/idm/data/summary", tgt, payload)

    def idm_weighted_average_price(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """GİP Ağırlıklı Ortalama Fiyat (IDM Weighted Average Price)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/idm/data/weighted-average-price", tgt, payload)

    # --- BPM (DGP) ---
    def smp(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """SMF Listeleme Servisi (SMP - System Marginal Price)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/bpm/data/smp", tgt, payload)

    def zero_balance(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Sıfır Bakiye Düzeltme Tutarı (Zero Balance)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/bpm/data/zero-balance", tgt, payload)

    # ==========================================
    # 8. TRANSMISSION (İLETİM) SERVICES
    # ==========================================

    def congestion_rent(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Kısıt Kira Geliri (Congestion Rent)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/transmission/data/congestion-rent", tgt, payload)

    def international_line_capacities(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Uluslararası Hat Kapasiteleri (International Line Capacities)"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/transmission/data/international-line-capacities", tgt, payload)

    # ==========================================
    # 9. YEK-G SERVICES
    # ==========================================

    def yek_g_list(self, tgt: str) -> requests.Response:
        """YEK-G Santral Listesi"""
        return self._post("v1/environmental-markets/yek-g/data/powerplant-list", tgt, {})

    def yek_g_market_clearing_price(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """YEK-G Piyasası Takas Fiyatı"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/environmental-markets/yek-g/data/mcp", tgt, payload)