# FUNCTION CALLING AGENT 

import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai
import os

from alpaca.broker import BrokerClient
from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from google import genai
from google.genai import types
from quantmodels.config import BROKER_API_KEY, GOOGLE_API_KEY, GEMINI_2_5_FLASH, BROKER_API_KEY, BROKER_SECRET_KEY

broker_client = BrokerClient(
    api_key=BROKER_API_KEY,
    secret_key=BROKER_SECRET_KEY,
    sandbox=True,
)

# Initialize the client and set your API key
client = genai.Client(api_key=GOOGLE_API_KEY)

# account to make order for
MODEL_ID = GEMINI_2_5_FLASH

# CREATE A CLASS FOR ORDER MANAGEMENT
class OrderManager:
    def __init__(self, broker_client, model_id):
        self.broker_client = broker_client
        self.MODEL_ID = model_id

    # CREATE METHOD TO PREPARE AND SUBMIT ORDERS
    def submit_market_order(self, symbol: str, qty: int, side: OrderSide, time_in_force: TimeInForce, commission: float):
        # preparing orders
        market_order_data = MarketOrderRequest(
                            symbol="AAPL",
                            qty=1,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.GTC,
                            commission=0
                    )


        # Market order
        market_order = broker_client.submit_order_for_account(
                        MODEL_ID=MODEL_ID,
                        order_data=market_order_data
                        )
# CALL THE ORDER MANAGER
order_manager = OrderManager(broker_client, MODEL_ID)
order_manager.submit_market_order(symbol="AAPL", qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.GTC, commission=0)    
