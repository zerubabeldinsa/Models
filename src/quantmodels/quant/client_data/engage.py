import warnings
warnings.filterwarnings("ignore")

import os
import sys
from pathlib import Path
from typing import Optional

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

class EngageAgent:
    """
    An agent that facilitates client engagement and portfolio management using 
    Alpaca Broker API and Google's Gemini GenAI model.
    """
    
    def __init__(
        self, 
        broker_api_key: str = BROKER_API_KEY, 
        broker_secret_key: str = BROKER_SECRET_KEY,
        google_api_key: str = GOOGLE_API_KEY,
        account_id: str = ACCOUNT_ID,
        model_id: str = GEMINI_2_5_FLASH,
        sandbox: bool = True
    ):
        self.account_id = account_id
        self.model_id = model_id
        
        # Initialize the Alpaca Broker Client
        self.broker_client = BrokerClient(
            api_key=broker_api_key,
            secret_key=broker_secret_key,
            sandbox=sandbox,
        )

        # Initialize the Gemini Client
        self.genai_client = genai.Client(api_key=google_api_key)
        
        # Initialize the chat session with automatic function calling
        self.chat = self._initialize_chat()

    def _initialize_chat(self):
        """
        Initializes a chat session with the specified tools and configuration.
        """
        operation_tools = [self.buy_stock_if_not_owned]
        
        return self.genai_client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                tools=operation_tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

    def buy_stock_if_not_owned(self, symbol: str, qty: int = 1) -> str:
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

        print(f"Checking if {symbol} is already in the portfolio for account {self.account_id}...")
        try:
            # Fetch current positions
            positions = self.broker_client.get_all_positions_for_account(self.account_id)
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
            order = self.broker_client.submit_order_for_account(
                account_id=self.account_id,
                order_data=market_order_data
            )
            
            return f"Successfully placed market order for {qty} shares of {symbol}. Order ID: {order.id}"
            
        except Exception as e:
            return f"Error processing request for {symbol}: {str(e)}"

    def send_message(self, message: str) -> str:
        """
        Sends a message to the Gemini model and returns the text response.
        The model can automatically call tools like buy_stock_if_not_owned.
        """
        try:
            response = self.chat.send_message(message=message)
            return response.text or "No text response received."
        except Exception as e:
            return f"An error occurred while communicating with the model: {e}"

if __name__ == "__main__":
    # Create an instance of the EngageAgent
    agent = EngageAgent()
    
    # Example execution
    ticker_to_check = "GOOGL"
    user_prompt = f"I want to buy 1 share of {ticker_to_check} if I don't already have it in my portfolio."
    
    print(f"Sending message to model: '{user_prompt}'")
    response_text = agent.send_message(user_prompt)
    print(f"\nModel Response: {response_text}")
