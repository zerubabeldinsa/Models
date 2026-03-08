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

# The client automatically picks up the API key from the environment variable
genai.configure(api_key="AIzaSyARCUJVHwY-gVCfnIqcDqdCDPAT9t1s8Y4")

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-3-flash-preview')

account_id = "8290bf23-8165-4b43-92ba-4339464815d1"

# positions = broker_client.get_all_positions_for_account(account_id)
# print(positions)


def get_active_positions(account_id: str):
    """Fetch all active positions for the given account.

    NOTE: In this environment, the BrokerClient may not expose a positions
    endpoint with the current API key/permissions. If you have a working
    method (e.g., get_all_positions_for_account), call it here instead of
    returning an empty list.
    """
    # Example (uncomment when available):
    # return broker_client.get_all_positions_for_account(account_id)
    return []


def summarize_positions(positions) -> dict:
    """Build a JSON summary of the client's active positioning.

    The summary focuses on:
    - total exposure and concentration
    - long vs short balance and directional bias
    - position-level P/L aggregates and winner/loser breakdown
    - diversification / concentration metrics
    """

    summary = {
        "totals": {
            "num_positions": 0,
            "total_long_market_value": 0.0,
            "total_short_market_value": 0.0,
            "gross_market_value": 0.0,
            "net_market_value": 0.0,
            "total_unrealized_pl": 0.0,
            "total_unrealized_pl_pct_weighted": 0.0,
        },
        "by_symbol": {},  # symbol -> {quantity, market_value, unrealized_pl, unrealized_pl_pct, side, weight}
        "concentration": {
            "top_symbol": None,
            "top_symbol_market_value": 0.0,
            "top_symbol_weight_pct": None,
        },
        "directional_bias": {
            "long_weight_pct": 0.0,
            "short_weight_pct": 0.0,
            "net_exposure_pct": 0.0,
        },
        "pl_breakdown": {
            "num_winning_positions": 0,
            "num_losing_positions": 0,
            "num_flat_positions": 0,
            "avg_unrealized_pl_pct_winners": 0.0,
            "avg_unrealized_pl_pct_losers": 0.0,
            "largest_winner_symbol": None,
            "largest_winner_unrealized_pl": 0.0,
            "largest_loser_symbol": None,
            "largest_loser_unrealized_pl": 0.0,
        },
        "diversification": {
            "herfindahl_index": 0.0,
            "effective_number_of_positions": 0.0,
        },
    }

    total_mv = 0.0
    total_unrealized_pl = 0.0

    # For PL breakdown
    winning_pl_pcts = []
    losing_pl_pcts = []
    largest_winner_pl = float("-inf")
    largest_winner_sym = None
    largest_loser_pl = float("inf")
    largest_loser_sym = None

    # positions/portfolio entries is expected to be an iterable of objects with symbol, qty, market_value, side, etc.
    for p in positions:
        symbol = getattr(p, "symbol", None)
        if symbol is None:
            # Skip any entries that do not look like position/holding objects
            continue

        qty = float(getattr(p, "qty", 0.0))
        mv = float(getattr(p, "market_value", 0.0))
        side = getattr(p, "side", "long")  # default to long if not present

        # Alpaca typically provides these fields on Position/Portfolio
        unrealized_pl = float(getattr(p, "unrealized_pl", 0.0))
        raw_unrealized_plpc = getattr(p, "unrealized_plpc", None)
        if raw_unrealized_plpc in (None, ""):
            unrealized_pl_pct = 0.0
        else:
            unrealized_pl_pct = float(raw_unrealized_plpc)

        summary["by_symbol"][symbol] = {
            "symbol": symbol,
            "quantity": qty,
            "market_value": mv,
            "side": side,
            "unrealized_pl": unrealized_pl,
            "unrealized_pl_pct": unrealized_pl_pct,
            # weight is filled in later once we know total_mv
            "weight_pct": 0.0,
        }

        summary["totals"]["num_positions"] += 1
        total_mv += mv
        total_unrealized_pl += unrealized_pl

        if side == "long":
            summary["totals"]["total_long_market_value"] += mv
        elif side == "short":
            summary["totals"]["total_short_market_value"] += mv

        # P/L breakdown stats
        if unrealized_pl > 0:
            summary["pl_breakdown"]["num_winning_positions"] += 1
            winning_pl_pcts.append(unrealized_pl_pct)
            if unrealized_pl > largest_winner_pl:
                largest_winner_pl = unrealized_pl
                largest_winner_sym = symbol
        elif unrealized_pl < 0:
            summary["pl_breakdown"]["num_losing_positions"] += 1
            losing_pl_pcts.append(unrealized_pl_pct)
            if unrealized_pl < largest_loser_pl:
                largest_loser_pl = unrealized_pl
                largest_loser_sym = symbol
        else:
            summary["pl_breakdown"]["num_flat_positions"] += 1

    # Compute derived totals
    summary["totals"]["gross_market_value"] = total_mv
    summary["totals"]["net_market_value"] = (
        summary["totals"]["total_long_market_value"] - summary["totals"]["total_short_market_value"]
    )
    summary["totals"]["total_unrealized_pl"] = total_unrealized_pl

    # Directional bias (as percent of gross MV)
    if total_mv > 0:
        long_mv = summary["totals"]["total_long_market_value"]
        short_mv = summary["totals"]["total_short_market_value"]
        summary["directional_bias"]["long_weight_pct"] = long_mv / total_mv
        summary["directional_bias"]["short_weight_pct"] = short_mv / total_mv
        summary["directional_bias"]["net_exposure_pct"] = (
            summary["totals"]["net_market_value"] / total_mv
        )

    # Compute concentration, weights, weighted unrealized P/L, and diversification
    top_symbol = None
    top_symbol_mv = 0.0
    weighted_pl_pct = 0.0
    herfindahl = 0.0

    for symbol, info in summary["by_symbol"].items():
        mv = info["market_value"]
        if total_mv > 0:
            weight = mv / total_mv
        else:
            weight = 0.0

        info["weight_pct"] = weight

        if mv > top_symbol_mv:
            top_symbol_mv = mv
            top_symbol = symbol

        if total_mv > 0:
            weighted_pl_pct += weight * info["unrealized_pl_pct"]
            herfindahl += weight ** 2

    summary["totals"]["total_unrealized_pl_pct_weighted"] = weighted_pl_pct if total_mv > 0 else 0.0

    if top_symbol is not None and total_mv > 0:
        summary["concentration"]["top_symbol"] = top_symbol
        summary["concentration"]["top_symbol_market_value"] = top_symbol_mv
        summary["concentration"]["top_symbol_weight_pct"] = top_symbol_mv / total_mv

    # Diversification metrics
    summary["diversification"]["herfindahl_index"] = herfindahl
    summary["diversification"]["effective_number_of_positions"] = (1.0 / herfindahl) if herfindahl > 0 else 0.0

    # P/L breakdown aggregates
    if winning_pl_pcts:
        summary["pl_breakdown"]["avg_unrealized_pl_pct_winners"] = sum(winning_pl_pcts) / len(winning_pl_pcts)
    if losing_pl_pcts:
        summary["pl_breakdown"]["avg_unrealized_pl_pct_losers"] = sum(losing_pl_pcts) / len(losing_pl_pcts)

    summary["pl_breakdown"]["largest_winner_symbol"] = largest_winner_sym
    summary["pl_breakdown"]["largest_winner_unrealized_pl"] = (
        largest_winner_pl if largest_winner_sym is not None else 0.0
    )
    summary["pl_breakdown"]["largest_loser_symbol"] = largest_loser_sym
    summary["pl_breakdown"]["largest_loser_unrealized_pl"] = (
        largest_loser_pl if largest_loser_sym is not None else 0.0
    )

    return summary


def interpret_positioning_with_model(summary: dict) -> str:
    """Use the Gemini model to generate a human-readable interpretation of the client's active positioning."""
    prompt = (
        "You are a trading and portfolio analysis assistant. "
        "Given the following JSON summary of a client's ACTIVE POSITIONS, "
        "explain in clear, concise terms what their positioning reveals about "
        "risk concentration, diversification (including the effective number of positions), "
        "long vs short balance and directional bias, and overall P/L across positions, including "
        "the balance of winners vs losers and the impact of the largest positions. "
        "If there are no positions, state that clearly and comment on the implications (e.g., sitting in cash). "
        "Do not restate every number.\n\n"
        "JSON summary:\n" + json.dumps(summary, indent=2)
    )

    response = model.generate_content(prompt)
    return getattr(response, "text", str(response))


if __name__ == "__main__":
    # If you have a working positions endpoint, you can switch this to:
    # positions = get_active_positions(account_id)
    positions = broker_client.get_all_positions_for_account(account_id)
    summary = summarize_positions(positions)
    print(json.dumps(summary, indent=2))
    print("\n--- Positioning Interpretation ---\n")
    interpretation = interpret_positioning_with_model(summary)
    print(interpretation)
