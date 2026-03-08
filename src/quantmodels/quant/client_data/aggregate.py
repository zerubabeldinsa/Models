import os
import sys
from pathlib import Path

# Add the 'src' directory to the Python path for direct script execution
src_path = str(Path(__file__).resolve().parents[3])
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import json
from alpaca.broker import BrokerClient
from quantmodels.config import BROKER_API_KEY, BROKER_SECRET_KEY, ACCOUNT_ID

import google.generativeai as genai

broker_client = BrokerClient(
    api_key=BROKER_API_KEY,
    secret_key=BROKER_SECRET_KEY,
    sandbox=True,
)

account_id = ACCOUNT_ID

data = broker_client.get_trade_account_by_id(account_id)
client_positioning = broker_client.get_all_positions_for_account(account_id)



