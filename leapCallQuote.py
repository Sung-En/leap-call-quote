import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime, timedelta
import re

def get_expiration_dates(symbol):
    """Fetches available expiration dates for the given symbol."""
    stock = yf.Ticker(symbol)
    expirations = stock.options
    return expirations


def get_default_expiration(expirations):
    """Get the default option expiration date (closest to one year from today)."""
    today = datetime.today()
    one_year_later = today + timedelta(days=365)
    default_expiration = min(expirations, key=lambda x: abs(datetime.strptime(x, '%Y-%m-%d') - one_year_later))
    return default_expiration


def fetch_option_data(symbol, expiration):
    """Fetches option chain data for the given symbol and expiration date."""
    stock = yf.Ticker(symbol)
    options = stock.option_chain(expiration)
    calls = options.calls
    current_price = stock.info['currentPrice']
    return calls, current_price


def calculate_leverage_ratios(calls, stock_price, gain_pct):
    """Calculates leverage ratios and adjusted leverage ratios for options."""
    strikes = calls['strike'].values
    premiums = calls['ask'].values

    leverage_ratios = stock_price / premiums

    future_price = stock_price * (1 + gain_pct / 100)
    intrinsic_gains = (future_price - strikes).clip(min=0)
    premium_gains = intrinsic_gains - premiums

    adjusted_ratios = (premium_gains / premiums) / (gain_pct / 100)

    return strikes, leverage_ratios, adjusted_ratios, premiums


def plot_leverage_ratios(strikes, leverage_ratios, adjusted_ratios, premiums, show_adjusted):
    """Plots leverage ratios and adjusted leverage ratios."""
    break_even_prices = strikes + premiums

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Primary x-axis and y-axis
    ax1.plot(strikes, leverage_ratios, label="Leverage Ratio", marker="o")
    if show_adjusted:
        ax1.plot(strikes, adjusted_ratios, label="Adjusted Leverage Ratio", marker="x")

    ax1.set_xlabel("Strike Price", fontsize=26)
    ax1.set_ylabel("Leverage Ratio", fontsize=26)
    ax1.set_title("Leverage Ratios vs. Strike Prices", fontsize=28)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=20)
    ax1.tick_params(axis="both", which="major", labelsize=20)  # Axis tick labels larger
    # Secondary x-axis for break-even prices
    ax2 = ax1.twiny()
    ax2.set_xlim(ax1.get_xlim())  # Align the x-axes
    ax2.set_xticks(strikes)
    ax2.set_xticklabels([f"{price:.1f}" for price in break_even_prices], rotation=45)  # Adjusted to 1 decimal place
    ax2.set_xlabel("Break-Even Price")
    ax2.tick_params(axis="both", which="major", labelsize=20)  # Axis tick labels larger

    plt.tight_layout()
    st.pyplot(fig)


def main():
    st.title("Option Leverage Plotter")

    # Stock symbol input
    symbol = st.text_input("Stock Symbol", "AAPL").upper()
    symbol = "".join(re.findall(r'[A-Za-z]+', symbol)).upper()

    # Fetch available expiration dates
    expirations = get_expiration_dates(symbol)
    default_expiration = get_default_expiration(expirations)

    # User input for expiration date selection
    expiration = st.selectbox("Select Expiration Date", expirations, index=expirations.index(default_expiration))

    # User inputs for target price
    stock_price = yf.Ticker(symbol).info['currentPrice']

    # Target price input using percentage and fixed value
    target_percentage = st.slider("Target Price Increase (%)", -100, 100, 20)
    target_price = stock_price * (1 + target_percentage / 100)

    # Display current and target prices
    st.write(f"Current Price: ${stock_price:.2f}")
    st.write(f"Target Price (after {target_percentage}% increase): ${target_price:.2f}")

    # Strike price range input (single slider)
    strike_range = st.slider("Strike Price Range (%)", -100, 20, (-50, -10), step=1)
    min_range, max_range = strike_range

    # Plot options
    show_adjusted = st.checkbox("Show Adjusted Leverage Ratio", value=True)

    # Fetch option data
    calls, _ = fetch_option_data(symbol, expiration)

    strikes, leverage_ratios, adjusted_ratios, premiums = calculate_leverage_ratios(
        calls, stock_price, target_percentage
    )

    # Filter strike prices based on selected range
    min_strike = stock_price * (1 + min_range / 100)
    max_strike = stock_price * (1 + max_range / 100)

    filtered_strikes = strikes[(strikes >= min_strike) & (strikes <= max_strike)]
    filtered_leverage_ratios = leverage_ratios[(strikes >= min_strike) & (strikes <= max_strike)]
    filtered_adjusted_ratios = adjusted_ratios[(strikes >= min_strike) & (strikes <= max_strike)]
    filtered_premiums = premiums[(strikes >= min_strike) & (strikes <= max_strike)]

    # Plot results
    plot_leverage_ratios(
        filtered_strikes, filtered_leverage_ratios, filtered_adjusted_ratios, filtered_premiums, show_adjusted
    )


if __name__ == "__main__":
    main()
