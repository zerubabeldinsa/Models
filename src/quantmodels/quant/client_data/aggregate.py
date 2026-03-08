
import json
from alpaca.broker import BrokerClient
from quantmodels.config import BROKER_API_KEY, BROKER_SECRET_KEY, ACCOUNT_ID

import google.generativeai as genai
import os

broker_client = BrokerClient(
    api_key=BROKER_API_KEY,
    secret_key=BROKER_SECRET_KEY,
    sandbox=True,
)

account_id = ACCOUNT_ID

data = broker_client.get_trade_account_by_id(account_id)
client_positioning = broker_client.get_all_positions_for_account(account_id)



