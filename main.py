import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Financial Analysis", layout="wide")

with st.sidebar:
    st.title("Financial Analysis")
    ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "AAPL")

    time_period_labels = {
        "1 Month": "1M",
        "3 Month": "3M",
        "6 Month": "6M",
        "1 Year": "1Y",
        "5 Year": "5Y"
    }

    period = st.selectbox(
        "Enter a time frame",
        list(time_period_labels.keys()),
        index=2
    )
    
    interval_options = {
        "5 Min": "5m",
        "30 Min": "30m",
        "1 Hr": "1h",
        "1 Day": "1d"
    }
    interval_choice = st.selectbox(
        "Select a Time Interval",
        list(interval_options.keys()),
        index=3
    )
    selected_interval = interval_options[interval_choice]

    show_sma = st.checkbox("Show 15 SMA", value=True)

    button = st.button("Submit")

def format_value(value):
    suffixes = ["", "K", "M", "B", "T"]
    suffix_index = 0
    while value and value >= 1000 and suffix_index < len(suffixes) - 1:
        value /= 1000
        suffix_index += 1
    return f"${value:.1f}{suffixes[suffix_index]}" if value else "N/A"

def safe_format(value, fmt="{:.2f}", fallback="N/A"):
    try:
        return fmt.format(value) if value is not None else fallback
    except (ValueError, TypeError):
        return fallback

period_map = {
    "1 Month": "1mo",
    "3 Month": "3mo",
    "6 Month": "6mo",
    "1 Year": "1y",
    "5 Year": "5y"
}

if button:
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    else:
        try:
            with st.spinner("Please wait..."):
                stock = yf.Ticker(ticker)
                info = stock.info

                st.subheader(f"{ticker} - {info.get('longName', 'N/A')}")

                selected_period = period_map.get(period, "1mo")

                history = stock.history(period=selected_period, interval=selected_interval)

                if history.empty:
                    st.warning(
                        f"No data returned for {ticker} with period='{selected_period}' "
                        f"and interval='{selected_interval}'. Some combinations "
                        "are not supported by Yahoo Finance."
                    )
                else:
                    #Added Functionality (15 SMA)
                    history['15 SMA'] = history['Close'].rolling(window=15).mean()
                    fig = go.Figure()

                    fig.add_trace(go.Scatter(
                        x=history.index,
                        y=history['Close'],
                        mode='lines',
                        name='Closing Price',
                        line=dict(color='blue', width=2)
                    ))
        
                    if show_sma:
                        fig.add_trace(go.Scatter(
                            x=history.index,
                            y=history['15 SMA'],
                            mode='lines',
                            name='15 SMA',
                            line=dict(color='red', width=1.5)
                        ))

                    y_min = history['Close'].min() * 0.95
                    y_max = history['Close'].max() * 1.05

                    fig.update_layout(
                        title=f"{ticker} - {info.get('longName', 'N/A')}",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        yaxis=dict(range=[y_min, y_max]),
                        legend_title="Legend",
                        height=500,
                        template="plotly_white"
                    )

                    st.plotly_chart(fig, use_container_width=True)

                col1, col2, col3 = st.columns(3)

                # 1) Basic Stock Info
                stock_info = [
                    ("Stock Info", "Value"),
                    ("Country", info.get('country', 'N/A')),
                    ("Sector", info.get('sector', 'N/A')),
                    ("Industry", info.get('industry', 'N/A')),
                    ("Market Cap", format_value(info.get('marketCap'))),
                    ("Enterprise Value", format_value(info.get('enterpriseValue'))),
                    ("Employees", info.get('fullTimeEmployees', 'N/A'))
                ]
                df_info = pd.DataFrame(stock_info[1:], columns=stock_info[0]).astype(str)
                col1.dataframe(df_info, width=400, hide_index=True)

                # 2) Price Info
                price_info = [
                    ("Price Info", "Value"),
                    ("Current Price", safe_format(info.get('currentPrice'), fmt="${:.2f}")),
                    ("Previous Close", safe_format(info.get('previousClose'), fmt="${:.2f}")),
                    ("Day High", safe_format(info.get('dayHigh'), fmt="${:.2f}")),
                    ("Day Low", safe_format(info.get('dayLow'), fmt="${:.2f}")),
                    ("52 Week High", safe_format(info.get('fiftyTwoWeekHigh'), fmt="${:.2f}")),
                    ("52 Week Low", safe_format(info.get('fiftyTwoWeekLow'), fmt="${:.2f}"))
                ]
                df_price = pd.DataFrame(price_info[1:], columns=price_info[0]).astype(str)
                col2.dataframe(df_price, width=400, hide_index=True)

                # 3) Business Metrics
                biz_metrics = [
                    ("Business Metrics", "Value"),
                    ("EPS (FWD)", safe_format(info.get('forwardEps'))),
                    ("P/E (FWD)", safe_format(info.get('forwardPE'))),
                    ("PEG Ratio", safe_format(info.get('pegRatio'))),
                    ("Div Rate (FWD)", safe_format(info.get('dividendRate'), fmt="${:.2f}")),
                    (
                        "Div Yield (FWD)",
                        safe_format(info.get('dividendYield') * 100, fmt="{:.2f}%")
                        if info.get('dividendYield') else 'N/A'
                    ),
                    ("Recommendation", info.get('recommendationKey', 'N/A').capitalize())
                ]
                df_biz = pd.DataFrame(biz_metrics[1:], columns=biz_metrics[0]).astype(str)
                col3.dataframe(df_biz, width=400, hide_index=True)

        except Exception as e:
            st.exception(f"An error occurred: {e}")