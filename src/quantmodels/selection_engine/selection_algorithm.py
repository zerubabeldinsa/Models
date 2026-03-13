import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ALPACA BROKERAGE API
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

# Add the 'src' directory to the Python path for direct script execution
src_path = str(Path(__file__).resolve().parents[2])
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from categories import cyclicals, non_cyclicals, growth, defensive
from quantmodels.config import API_KEY, API_SECRET

client = StockHistoricalDataClient(API_KEY, API_SECRET)

# CORE ENGINE #
categories = {
    "cyclicals": cyclicals,
    "non_cyclicals": non_cyclicals,
    "growth": growth,
    "defensive": defensive
}


def get_price_data(symbols):

    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=datetime.now() - timedelta(days=365)
    )

    bars = client.get_stock_bars(request)

    df = bars.df.reset_index()

    prices = df.pivot(index="timestamp", columns="symbol", values="close")

    return prices


# HRP SELECTION FUNCTION #
def hrp_selection(prices, n_assets=5):

    returns = prices.pct_change().dropna()

    corr = returns.corr()

    # Distance matrix
    dist = np.sqrt(0.5 * (1 - corr))

    link = linkage(squareform(dist), method="ward")

    dendro = dendrogram(link, labels=corr.columns, no_plot=True)

    ordered_assets = dendro["ivl"]

    selected = ordered_assets[:n_assets]

    return selected, corr

# PORTFOLIO BUILDER
def build_daily_portfolios():

    portfolios = {}

    for category, stock_list in categories.items():

        sample_size = min(5, len(stock_list))
        sampled_symbols = random.sample(stock_list, sample_size) if sample_size > 0 else []

        prices = get_price_data(sampled_symbols)

        selected, corr = hrp_selection(prices, n_assets=min(5, prices.shape[1]))

        portfolios[category] = selected

    return portfolios

# CORRELATION DATA FOR RANDOMLY SAMPLED STOCKS
def get_random_sample_correlation(category, sample_size=5):

    stock_list = categories.get(category, [])
    sample_size = min(sample_size, len(stock_list))
    sampled_symbols = random.sample(stock_list, sample_size) if sample_size > 0 else []

    if not sampled_symbols:
        return sampled_symbols, pd.DataFrame()

    prices = get_price_data(sampled_symbols)
    returns = prices.pct_change().dropna()
    corr = returns.corr()

    return sampled_symbols, corr

# DAILY OUTPUT
def run_daily():

    portfolios = build_daily_portfolios()

    print("\nDaily Diversified Portfolios\n")

    for category, stocks in portfolios.items():

        print(category.upper())
        print(stocks)
        print()

if __name__ == "__main__":
    run_daily()

