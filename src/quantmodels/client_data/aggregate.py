
import json
from alpaca.broker import BrokerClient

import google.generativeai as genai
import os


BROKER_API_KEY = "CKTUXDBUQTSU5BCI0RFU"
BROKER_SECRET_KEY = "mEENVmXhTCM2gZMx0Ds7RjrUbNBi9Gm7ZTA3P5xR"

broker_client = BrokerClient(
    api_key=BROKER_API_KEY,
    secret_key=BROKER_SECRET_KEY,
    sandbox=True,
)

account_id = "8290bf23-8165-4b43-92ba-4339464815d1"

data = broker_client.get_trade_account_by_id(account_id)
client_positioning = broker_client.get_all_positions_for_account(account_id)



