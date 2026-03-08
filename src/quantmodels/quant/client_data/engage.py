import warnings
warnings.filterwarnings("ignore")

import os
import sys
from pathlib import Path

# Add the 'src' directory to the Python path for direct script execution
src_path = str(Path(__file__).resolve().parents[3])
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from google import genai
from google.genai import types
from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from quantmodels.config import (
    BROKER_API_KEY, 
    BROKER_SECRET_KEY, 
    GOOGLE_API_KEY, 
    ACCOUNT_ID, 
    GEMINI_2_5_FLASH
)

# Initialize the Alpaca Broker Client
broker_client = BrokerClient(
    api_key=BROKER_API_KEY,
    secret_key=BROKER_SECRET_KEY,
    sandbox=True,
)

# Initialize the Gemini Client
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = GEMINI_2_5_FLASH

def buy_stock_if_not_owned(symbol: str, qty: int = 1):
    """
    Checks if a stock ticker symbol already exists in the client's portfolio.
    If it doesn't exist, places a market order to buy the specified quantity.
    
    Args:
        symbol: The ticker symbol of the stock to buy (e.g., 'AAPL').
        qty: The number of shares to buy. Defaults to 1.
    """
    if not symbol:
        return "Error: No symbol provided."
    
    symbol = symbol.strip().upper()
    try:
        qty = int(qty)
    except (ValueError, TypeError):
        qty = 1

    print(f"Checking if {symbol} is already in the portfolio for account {ACCOUNT_ID}...")
    try:
        # Fetch current positions
        positions = broker_client.get_all_positions_for_account(ACCOUNT_ID)
        if positions is None:
            positions = []
        
        # Check if symbol is already in portfolio
        already_owned = any(getattr(p, 'symbol', None) == symbol for p in positions)
        
        if already_owned:
            return f"Client already owns {symbol}. No new order placed."
        
        print(f"{symbol} not found in portfolio. Placing market order for {qty} share(s).")
        
        # Prepare market order
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )

        # Submit the order
        order = broker_client.submit_order_for_account(
            account_id=ACCOUNT_ID,
            order_data=market_order_data
        )
        
        return f"Successfully placed market order for {qty} shares of {symbol}. Order ID: {order.id}"
        
    except Exception as e:
        return f"Error processing request for {symbol}: {str(e)}"

# Define the tools for the Gemini model
operation_tools = [buy_stock_if_not_owned]

# Initialize a chat session with automatic function calling enabled
chat = client.chats.create(
    model=MODEL_ID,
    config=types.GenerateContentConfig(
        tools=operation_tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )
)

if __name__ == "__main__":
    # Example execution: "I want to buy 1 share of AAPL if I don't already have it."
    # The model will call buy_stock_if_not_owned automatically.
    ticker_to_check = "GOOGL"
    print(f"Sending message to model: 'I want to buy 1 share of {ticker_to_check} if I don't already have it.'")
    
    try:
        response = chat.send_message(
            message=f"I want to buy 1 share of {ticker_to_check} if I don't already have it in my portfolio."
        )
        print(f"\nModel Response: {response.text or 'No text response received.'}")
    except Exception as e:
        print(f"\nAn error occurred while communicating with the model: {e}")
