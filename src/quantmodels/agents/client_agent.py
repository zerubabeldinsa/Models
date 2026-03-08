# FUNCTION CALLING AGENT 

import warnings
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types
from quantmodels.config import GOOGLE_API_KEY, GEMINI_2_5_FLASH

# Initialize the client and set your API key
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = GEMINI_2_5_FLASH

def add(a: float, b: float):
    """Returns the sum of two numbers.
    
    Args:
        a: The first number.
        b: The second number.
    """
    return a + b

def subtract(a: float, b: float):
    """Returns the difference of two numbers.
    
    Args:
        a: The first number.
        b: The second number (subtrahend).
    """
    return a - b

def multiply(a: float, b: float):
    """Returns the product of two numbers.
    
    Args:
        a: The first number.
        b: The second number.
    """
    return a * b

def divide(a: float, b: float):
    """Returns the quotient of two numbers.
    
    Args:
        a: The dividend.
        b: The divisor.
    """
    if b == 0:
        return "Cannot divide by zero."
    return a / b

# Define the tools
operation_tools = [add, subtract, multiply, divide]

# Initialize a chat session with automatic function calling enabled via config object
chat = client.chats.create(
    model=MODEL_ID,
    config=types.GenerateContentConfig(
        tools=operation_tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )
)

# Send a message that requires multiple tool calls
# (57 * 44)
response = chat.send_message(
    message="I have 57 cats, each owns 44 mittens, how many mittens is that in total?"
)

# In automatic function calling mode, the final response is the text result
print(f"Response: {response.text}")
