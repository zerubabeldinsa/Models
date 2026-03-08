import json
from alpaca.broker import BrokerClient
from quantmodels.config import BROKER_API_KEY, BROKER_SECRET_KEY, GOOGLE_API_KEY, ACCOUNT_ID, GEMINI_3_FLASH_PREVIEW

import google.generativeai as genai
import os

broker_client = BrokerClient(
    api_key=BROKER_API_KEY,
    secret_key=BROKER_SECRET_KEY,
    sandbox=True,
)

# The client automatically picks up the API key from the environment variable
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel(GEMINI_3_FLASH_PREVIEW)

account_id = ACCOUNT_ID
data = broker_client.get_trade_account_by_id(account_id)
client_positioning = broker_client.get_all_positions_for_account(account_id)

print(client_positioning)

def summarize_trade_account(a) -> dict:
    equity = float(a.equity)
    cash = float(a.cash)
    long_mv = float(a.long_market_value)
    buying_power = float(a.buying_power)
    initial_margin = float(a.initial_margin)
    maintenance_margin = float(a.maintenance_margin)
    cash_withdrawable = float(a.cash_withdrawable)
    cash_transferable = float(a.cash_transferable)

    last_equity = float(a.last_equity)
    last_long_mv = float(a.last_long_market_value)
    last_cash = float(a.last_cash)

    def pct(n, d):
        return n / d if d else None

    allocation_cash_pct = pct(cash, equity)
    allocation_invested_pct = pct(long_mv, equity)

    margin_leverage_ratio = pct(buying_power, equity)
    margin_usage_to_equity = pct(initial_margin, equity)
    maintenance_margin_to_equity = pct(maintenance_margin, equity)

    liquidity_cash_withdrawable_pct = pct(cash_withdrawable, equity)
    liquidity_cash_transferable_pct = pct(cash_transferable, equity)

    # Simple P/L over the last snapshot period (typically since previous_close)
    period_pnl = equity - last_equity
    period_pnl_pct = pct(period_pnl, last_equity)

    return {
        "allocation": {
            "equity": equity,
            "cash": cash,
            "long_market_value": long_mv,
            "cash_pct_of_equity": allocation_cash_pct,
            "invested_pct_of_equity": allocation_invested_pct,
        },
        "margin": {
            "buying_power": buying_power,
            "initial_margin": initial_margin,
            "maintenance_margin": maintenance_margin,
            "leverage_ratio": margin_leverage_ratio,
            "margin_usage_to_equity": margin_usage_to_equity,
            "maintenance_margin_to_equity": maintenance_margin_to_equity,
        },
        "liquidity": {
            "cash_withdrawable": cash_withdrawable,
            "cash_transferable": cash_transferable,
            "cash_withdrawable_pct_of_equity": liquidity_cash_withdrawable_pct,
            "cash_transferable_pct_of_equity": liquidity_cash_transferable_pct,
        },
        "status": {
            "pattern_day_trader": a.pattern_day_trader,
            "trading_blocked": a.trading_blocked,
            "transfers_blocked": a.transfers_blocked,
            "account_blocked": a.account_blocked,
            "trade_suspended_by_user": a.trade_suspended_by_user,
            "daytrade_count": a.daytrade_count,
        },
        "exposure": {
            "shorting_enabled": a.shorting_enabled,
            "short_market_value": float(a.short_market_value),
        },
        "performance": {
            "period_pnl": period_pnl,
            "period_pnl_pct": period_pnl_pct,
            "equity_current": equity,
            "equity_previous": last_equity,
            "long_market_value_current": long_mv,
            "long_market_value_previous": last_long_mv,
            "cash_current": cash,
            "cash_previous": last_cash,
        },
        "stability_since_last_close": {
            "equity": equity,
            "last_equity": last_equity,
            "equity_change_since_last": equity - last_equity,
            "long_market_value": long_mv,
            "last_long_market_value": last_long_mv,
            "long_mv_change_since_last": long_mv - last_long_mv,
            "cash": cash,
            "last_cash": last_cash,
            "cash_change_since_last": cash - last_cash,
            "daytrade_count": a.daytrade_count,
            "last_daytrade_count": a.last_daytrade_count,
            "daytrades_since_last": a.daytrade_count - a.last_daytrade_count,
        },
    }


def interpret_summary_with_model(summary: dict) -> str:
    """Use the Gemini model to generate a human-readable interpretation of the summary JSON."""
    prompt = (
        "You are a trading and portfolio analysis assistant. "
        "Given the following JSON summary of a client's brokerage account, "
        "explain in clear, concise terms what it reveals about the client's "
        "risk posture, leverage, liquidity, activity level, performance (P/L versus the previous period), "
        "and overall account health. Focus on key takeaways, including whether the portfolio has been "
        "outperforming or underperforming over the measured period. Do not restate every number.\n\n"
        "JSON summary:\n" + json.dumps(summary, indent=2)
    )

    response = model.generate_content(prompt)
    return getattr(response, "text", str(response))


if __name__ == "__main__":
    summary = summarize_trade_account(data)
    print(json.dumps(summary, indent=2))
    print("\n--- Interpretation ---\n")
    interpretation = interpret_summary_with_model(summary)
    print(interpretation)
