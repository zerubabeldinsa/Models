import requests
import os
import sys
from pathlib import Path

# Add the 'src' directory to the Python path for direct script execution
src_path = str(Path(__file__).resolve().parents[3])
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import json
from alpaca.broker import BrokerClient
from quantmodels.config import BROKER_API_KEY, BROKER_SECRET_KEY, GOOGLE_API_KEY, ACCOUNT_ID, GEMINI_3_FLASH_PREVIEW

# BROKERAGE ACCOUNT #
BROKER_API_KEY="CKTUXDBUQTSU5BCI0RFU"
BROKER_SECRET_KEY="mEENVmXhTCM2gZMx0Ds7RjrUbNBi9Gm7ZTA3P5xR"
BASE_URL = "https://broker-api.sandbox.alpaca.markets/"


# TRADING DETAILS
def trading_details(ACCOUNT_ID):
   
    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{ACCOUNT_ID}/account"
    headers = {
        "APCA-API-KEY-ID": BROKER_API_KEY,
        "APCA-API-SECRET-KEY": BROKER_SECRET_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    print(response.text)

trading_details(ACCOUNT_ID)

