import json
import sys
from pathlib import Path

import requests
from requests import RequestException

# Add the 'src' directory to the Python path for direct script execution
src_path = str(Path(__file__).resolve().parents[3])
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from quantmodels.config import ACCOUNT_ID, BROKER_API_KEY, BROKER_SECRET_KEY


def trading_details(account_id: str) -> dict:
    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{account_id}/account"
    headers = {
        "APCA-API-KEY-ID": BROKER_API_KEY,
        "APCA-API-SECRET-KEY": BROKER_SECRET_KEY,
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_response": response.text}

        return {
            "account_id": account_id,
            "request": {
                "url": url,
                "headers": {
                    "accept": headers["accept"],
                    "Content-Type": headers["Content-Type"],
                },
            },
            "response": {
                "ok": response.ok,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": payload,
            },
        }
    except RequestException as exc:
        response = getattr(exc, "response", None)

        if response is not None:
            try:
                payload = response.json()
            except ValueError:
                payload = {"raw_response": response.text}
        else:
            payload = None

        return {
            "account_id": account_id,
            "request": {
                "url": url,
                "headers": {
                    "accept": headers["accept"],
                    "Content-Type": headers["Content-Type"],
                },
            },
            "response": {
                "ok": False,
                "status_code": response.status_code if response is not None else None,
                "headers": dict(response.headers) if response is not None else {},
                "data": payload,
            },
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        }


if __name__ == "__main__":
    details = trading_details(ACCOUNT_ID)
    print(json.dumps(details, indent=2))
