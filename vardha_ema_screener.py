import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf


# ============================================================
# VARDHA EMA CROSSOVER SCREENER
# Daily timeframe | NSE Equity universe | EMA 21/50/100/200
# ============================================================

st.set_page_config(
    page_title="Vardha EMA Crossover Screener",
    page_icon="📈",
    layout="wide",
)

NSE_EQUITY_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

# User-defined strategy
EMA_FAST = 21
EMA_MID = 50
EMA_BASE = 100
EMA_BEST = 200

# 21/50 crossovers must occur within this many trading sessions.
MAX_CROSS_GAP = 5

# Download enough history for a meaningful 200 EMA.
YF_PERIOD = "2y"
BATCH_SIZE = 50

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/csv,text/plain,*/*",
    "Referer": "https://www.nseindia.com/",
}


# -----------------------------
# Helpers
# -----------------------------
def clean_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        # For single-ticker data, flatten the second level if possible.
        if len(df.columns.levels) >= 2:
            df.columns = [
                c[0] if str(c[1]) == "" else c[0]
                for c in df.columns
            ]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def fmt_num(x, digits=2):
    if pd.isna(x):
        return "-"
    return f"{x:.{digits}f}"


def cross_up(fast, slow):
    return (fast > slow) & (fast.shift(1) <= slow.shift(1))


def cross_down(fast, slow):
    return (fast < slow) & (fast.shift(1) >= slow.shift(1))


def recent_cross(series_bool, max_bars):
    """
    Returns:
      True if the most recent True is within max_bars,
      otherwise False.
    Also returns the bars since the latest cross.
    """
    idx = np.flatnonzero(series_bool.to_numpy(dtype=bool))
    if len(idx) == 0:
        return False, None
    bars_ago = len(series_bool) - 1 - idx[-1]
    return bars_ago <= max_bars, int(bars_ago)


def latest_cross_date(series_bool):
    hits = series_bool[series_bool]
    if hits.empty:
        return None
    return hits.index[-1]


def analyze_symbol(symbol, df):
    try:
        if df is None or df.empty:
            return None

        df = df.copy()
        df = clean_columns(df)

        required = {"Close"}
        if not required.issubset(df.columns):
            return None

        df = df[["Close"]].dropna()
        if len(df) < EMA_BEST + 20:
            return None

        close = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if len(close) < EMA_BEST + 20:
            return None

        ema21 = close.ewm(span=EMA_FAST, adjust=False).mean()
        ema50 = close.ewm(span=EMA_MID, adjust=False).mean()
        ema100 = close.ewm(span=EMA_BASE, adjust=False).mean()
        ema200 = close.ewm(span=EMA_BEST, adjust=False).mean()

        up21 = cross_up(ema21, ema100)
        up50 = cross_up(ema50, ema100)
        down21 = cross_down(ema21, ema100)
        down50 = cross_down(ema50, ema100)

        bull21_recent, bull21_age = recent_cross(up21, MAX_CROSS_GAP)
        bull50_recent, bull50_age = recent_cross(up50, MAX_CROSS_GAP)
        bear21_recent, bear21_age = recent_cross(down21, MAX_CROSS_GAP)
        bear50_recent, bear50_age = recent_cross(down50, MAX_CROSS_GAP)

        # Core strategy:
        # Both EMA21 and EMA50 must cross EMA100 in the same direction
        # within MAX_CROSS_GAP trading sessions.
        bull_core = bull21_recent and bull50_recent
        bear_core = bear21_recent and bear50_recent

        # 200 EMA confirmation:
        # Best/Strong signal when the 21/50/100 structure has also crossed
        # EMA200 in the same direction recently.
        up100_200 = cross_up(ema100, ema200)
        down100_200 = cross_down(ema100, ema200)

        bull200_recent, bull200_age = recent_cross(up100_200, MAX_CROSS_GAP)
        bear200_recent, bear200_age = recent_cross(down100_200, MAX_CROSS_GAP)

        strong_buy = bull_core and bull200_recent
        strong_sell = bear_core and bear200_recent

        # Current structure (useful for context, not a replacement for crossover)
        current_bull_structure = (
            ema21.iloc[-1] > ema50.iloc[-1] > ema100.iloc[-1]
        )
        current_bear_structure = (
            ema21.iloc[-1] < ema50.iloc[-1] < ema100.iloc[-1]
        )

        if strong_buy:
            signal = "STRONG BUY"
            rank = 1
        elif bull_core:
            signal = "BUY"
            rank = 2
        elif strong_sell:
            signal = "STRONG SELL"
            rank = 3
        elif bear_core:
            signal = "SELL"
            rank = 4
        else:
            # Watch only setups that are close to completing.
            bull_partial = (
                (bull21_recent and not bull50_recent)
                or (bull50_recent and not bull21_recent)
            )
            bear_partial = (
                (bear21_recent and not bear50_recent)
                or (bear50_recent and not bear21_recent)
            )

            if bull_partial or bear_partial:
                signal = "WATCH"
                rank = 5
            else:
                signal = "NO SIGNAL"
                rank = 6

        latest_bull_date = max(
            [d for d in [latest_cross_date(up21), latest_cross_date(up50)] if d is not None],
            default=None,
        )
        latest_bear_date = max(
            [d for d in [latest_cross_date(down21), latest_cross_date(down50)] if d is not None],
            default=None,
        )

        # For a BUY/SELL result, show the latest of the two required crosses.
        if "BUY" in signal:
            crossover_date = latest_bull_date
        elif "SELL" in signal:
            crossover_date = latest_bear_date
        else:
            crossover_date = latest_bull_date or latest_bear_date

        close_now = float(close.iloc[-1])

        # Simple risk levels based on EMA100/EMA200 structure.
        if "BUY" in signal:
            stop = min(float(ema100.iloc[-1]), float(ema200.iloc[-1]))
            if stop >= close_now:
                stop = float(ema100.iloc[-1]) * 0.98
            risk = max(close_now - stop, close_now * 0.01)
            target1 = close_now + risk * 1.5
            target2 = close_now + risk * 2.5
        elif "SELL" in signal:
            stop = max(float(ema100.iloc[-1]), float(ema200.iloc[-1]))
            if stop <= close_now:
                stop = float(ema100.iloc[-1]) * 1.02
            risk = max(stop - close_now, close_now * 0.01)
            target1 = close_now - risk * 1.5
            target2 = close_now - risk * 2.5
        else:
            stop = np.nan
            target1 = np.nan
            target2 = np.nan

        return {
            "Ticker": symbol.replace(".NS", ""),
            "Price": close_now,
            "EMA21": float(ema21.iloc[-1]),
            "EMA50": float(ema50.iloc[-1]),
            "EMA100": float(ema100.iloc[-1]),
            "EMA200": float(ema200.iloc[-1]),
            "21×100": "YES" if bull21_recent or bear21_recent else "NO",
            "50×100": "YES" if bull50_recent or bear50_recent else "NO",
            "21×100 Age": bull21_age if bull21_recent else (bear21_age if bear21_recent else np.nan),
            "50×100 Age": bull50_age if bull50_recent else (bear50_age if bear50_recent else np.nan),
            "200 Confirm": (
                "BULLISH" if bull200_recent else
                "BEARISH" if bear200_recent else "NO"
            ),
            "Crossover Date": (
                crossover_date.strftime("%d-%b-%Y")
                if crossover_date is not None else "-"
            ),
            "Signal": signal,
            "Stop Loss": stop,
            "Target 1": target1,
            "Target 2": target2,
            "_rank": rank,
            "_bull_structure": current_bull_structure,
            "_bear_structure": current_bear_structure,
        }

    except Exception:
        return None


# -----------------------------
# NSE universe
# -----------------------------
@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def load_nse_equity_symbols():
    try:
        r = requests.get(NSE_EQUITY_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()

        df = pd.read_csv(io.BytesIO(r.content))
        df.columns = [str(c).strip().upper() for c in df.columns]

        # NSE's equity file normally contains SYMBOL and SERIES.
        if "SYMBOL" not in df.columns:
            raise ValueError("NSE equity CSV does not contain SYMBOL column.")

        if "SERIES" in df.columns:
            df = df[df["SERIES"].astype(str).str.upper().eq("EQ")]

        symbols = (
            df["SYMBOL"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace("", np.nan)
            .dropna()
            .drop_duplicates()
            .tolist()
        )

        # Exclude obvious non-company/index style symbols if they appear.
        symbols = [
            s for s in symbols
            if s.isalnum() or "-" in s or "&" in s
        ]

        return sorted(symbols)

    except Exception as e:
        st.error(f"NSE universe load failed: {e}")
        return []


# -----------------------------
# Yahoo Finance batch download
# -----------------------------
def download_batch(symbols):
    yf_symbols = [s + ".NS" for s in symbols]

    try:
        data = yf.download(
            tickers=yf_symbols,
            period=YF_PERIOD,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="ticker",
        )
        return data
    except Exception:
        return None


def extract_close_from_batch(data, symbol_ns):
    if data is None or data.empty:
        return None

    try:
        if isinstance(data.columns, pd.MultiIndex):
            # group_by="ticker" => (ticker, field)
            if symbol_ns in data.columns.get_level_values(0):
                part = data[symbol_ns]
                if "Close" in part.columns:
                    return part[["Close"]].dropna()

            # Some yfinance versions return (field, ticker)
            if "Close" in data.columns.get_level_values(0):
                part = data["Close"]
                if symbol_ns in part.columns:
                    return pd.DataFrame({"Close": part[symbol_ns]}).dropna()

        else:
            if "Close" in data.columns:
                return data[["Close"]].dropna()

    except Exception:
        pass

    return None


def run_scan(symbols, max_workers=4):
    results = []
    total = len(symbols)

    progress = st.progress(0, text="Starting scan...")
    status = st.empty()

    # Download in batches to avoid thousands of individual Yahoo requests.
    batches = [
        symbols[i:i + BATCH_SIZE]
        for i in range(0, len(symbols), BATCH_SIZE)
    ]

    completed = 0

    for batch_no, batch in enumerate(batches, start=1):
        status.info(
            f"Downloading batch {batch_no}/{len(batches)} "
            f"({len(batch)} stocks)..."
        )

        data = download_batch(batch)

        if data is not None and not data.empty:
            for symbol in batch:
                symbol_ns = symbol + ".NS"
                df = extract_close_from_batch(data, symbol_ns)

                result = analyze_symbol(symbol_ns, df)
                if result is not None:
                    results.append(result)

        completed += len(batch)
        progress.progress(
            min(completed / max(total, 1), 1.0),
            text=f"Processed {completed}/{total} stocks",
        )

        # Small pause helps reduce rate-limit pressure.
        time.sleep(0.15)

    progress.empty()
    status.empty()

    return pd.DataFrame(results)


# -----------------------------
# UI
# -----------------------------
st.title("📈 Vardha EMA Crossover Screener")
st.caption(
    "Daily (1D) NSE equity scanner • EMA 21 / 50 / 100 / 200 • "
    "Fresh crossover strategy"
)

with st.sidebar:
    st.header("⚙️ Strategy Settings")

    max_gap = st.slider(
        "Maximum crossover gap (days)",
        min_value=1,
        max_value=10,
        value=MAX_CROSS_GAP,
        help="EMA 21 and EMA 50 must cross EMA 100 within this many daily candles.",
    )

    st.markdown("---")
    st.write("**Mandatory BUY:** EMA 21 ↑ EMA 100 + EMA 50 ↑ EMA 100")
    st.write("**Mandatory SELL:** EMA 21 ↓ EMA 100 + EMA 50 ↓ EMA 100")
    st.write("**BEST:** same setup + EMA 100 crosses EMA 200")
    st.markdown("---")

    scan_all = st.checkbox(
        "Scan complete NSE Equity universe",
        value=True,
    )

    show_no_signal = st.checkbox(
        "Show NO SIGNAL stocks",
        value=False,
    )

    if st.button("🔄 Clear cached NSE universe"):
        load_nse_equity_symbols.clear()
        st.rerun()

symbols = load_nse_equity_symbols()

if not symbols:
    st.error("NSE stock list could not be loaded.")
    st.stop()

st.info(
    f"**NSE Equity universe loaded: {len(symbols)} stocks**. "
    "The scanner uses the official NSE securities-available-for-trading equity list."
)

if "scan_results" not in st.session_state:
    st.session_state.scan_results = None

if st.button("🚀 SCAN NSE STOCKS", type="primary", use_container_width=True):
    # Update global crossover window from the sidebar.
    globals()["MAX_CROSS_GAP"] = max_gap

    if scan_all:
        scan_symbols = symbols
    else:
        scan_symbols = symbols[:500]

    with st.spinner("Scanning daily EMA strategy..."):
        st.session_state.scan_results = run_scan(scan_symbols)

df = st.session_state.scan_results

if df is None:
    st.warning("Click **SCAN NSE STOCKS** to start the daily EMA scan.")
    st.stop()

if df.empty:
    st.warning("No valid stock data was returned. Try scanning again.")
    st.stop()

# Filter visible results
if not show_no_signal:
    display_df = df[df["Signal"] != "NO SIGNAL"].copy()
else:
    display_df = df.copy()

# Sort strongest signals first.
display_df = display_df.sort_values(
    by=["_rank", "Crossover Date"],
    ascending=[True, False],
    na_position="last",
)

# Metrics
strong_buy_count = int((df["Signal"] == "STRONG BUY").sum())
buy_count = int((df["Signal"] == "BUY").sum())
strong_sell_count = int((df["Signal"] == "STRONG SELL").sum())
sell_count = int((df["Signal"] == "SELL").sum())
watch_count = int((df["Signal"] == "WATCH").sum())

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Stocks Scanned", len(symbols) if scan_all else min(500, len(symbols)))
c2.metric("Strong BUY", strong_buy_count)
c3.metric("BUY", buy_count)
c4.metric("Strong SELL", strong_sell_count)
c5.metric("SELL", sell_count)
c6.metric("WATCH", watch_count)

st.markdown("### 🎯 Strategy Signals")

if display_df.empty:
    st.success(
        "No fresh EMA crossover setup found in the scanned universe."
    )
else:
    cols = [
        "Ticker",
        "Price",
        "EMA21",
        "EMA50",
        "EMA100",
        "EMA200",
        "21×100",
        "50×100",
        "200 Confirm",
        "Crossover Date",
        "Signal",
        "Stop Loss",
        "Target 1",
        "Target 2",
    ]

    st.dataframe(
        display_df[cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="%.2f"),
            "EMA21": st.column_config.NumberColumn(format="%.2f"),
            "EMA50": st.column_config.NumberColumn(format="%.2f"),
            "EMA100": st.column_config.NumberColumn(format="%.2f"),
            "EMA200": st.column_config.NumberColumn(format="%.2f"),
            "Stop Loss": st.column_config.NumberColumn(format="%.2f"),
            "Target 1": st.column_config.NumberColumn(format="%.2f"),
            "Target 2": st.column_config.NumberColumn(format="%.2f"),
        },
    )

st.markdown("### 📌 Core Rule")
st.write(
    f"Fresh daily crossover only. EMA 21 and EMA 50 must cross EMA 100 "
    f"in the same direction within **{max_gap} trading sessions**. "
    "EMA 100 crossing EMA 200 in the same direction upgrades the setup "
    "to **STRONG BUY / STRONG SELL**."
)

st.caption(
    "Educational/research tool — not investment advice. "
    "Prices and signals can change after the market closes and when new data is available."
)

# CSV download
csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Signals CSV",
    data=csv,
    file_name="vardha_ema_signals.csv",
    mime="text/csv",
)
