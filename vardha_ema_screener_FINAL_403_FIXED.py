
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# ============================================================
# VARDHA EMA CROSSOVER SCREENER V3 - FINAL
# Daily (1D) | NSE Equity Universe | EMA 21 / 50 / 100 / 200
#
# Strategy:
#   CORE BUY  = EMA21 crosses ABOVE EMA100 + EMA50 crosses ABOVE EMA100
#               within a small number of trading sessions.
#   CORE SELL = exact opposite.
#
#   STRONG BUY/SELL = CORE setup + EMA100/EMA200 crossover confirmation
#                     within a configurable window BEFORE or AFTER the core.
#
#   WATCH = only a fresh partial 21/50 -> 100 crossover; no broad watchlist.
#
# This is an educational/research scanner, not investment advice.
# ============================================================

st.set_page_config(
    page_title="Vardha EMA Crossover Screener V3",
    page_icon="📈",
    layout="wide",
)

# NSE's archive CSV can return HTTP 403 from some cloud IP ranges.
# The loader below uses several official NSE routes plus a mirror fallback.
NSE_EQUITY_URLS = [
    "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
    "https://www.nseindia.com/content/equities/EQUITY_L.csv",
    "https://www1.nseindia.com/content/equities/EQUITY_L.csv",
]
NSE_SECURITY_PAGE = "https://www.nseindia.com/market-data/securities-available-for-trading"

# Last-resort public mirror. Used only if NSE blocks the Streamlit Cloud IP.
NSE_MIRROR_URLS = [
    "https://raw.githubusercontent.com/feroze/YFinance-stock-history/master/EQUITY_L.csv",
]

EMA_FAST = 21
EMA_MID = 50
EMA_BASE = 100
EMA_BEST = 200

YF_PERIOD = "2y"
BATCH_SIZE = 40

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/csv,text/plain,*/*",
    "Referer": "https://www.nseindia.com/",
}


def clean_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        # Handles both (ticker, field) and (field, ticker).
        if len(df.columns.levels) >= 2:
            df.columns = [
                str(c[0]) if str(c[1]) == "" else str(c[0])
                for c in df.columns
            ]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def cross_up(fast, slow):
    return (fast > slow) & (fast.shift(1) <= slow.shift(1))


def cross_down(fast, slow):
    return (fast < slow) & (fast.shift(1) >= slow.shift(1))


def latest_cross_info(signal_series):
    idx = np.flatnonzero(signal_series.fillna(False).to_numpy(dtype=bool))
    if len(idx) == 0:
        return None, None
    i = int(idx[-1])
    age = len(signal_series) - 1 - i
    return i, int(age)


def analyze_symbol(
    symbol,
    df,
    core_gap=5,
    core_validity=15,
    best_window=20,
):
    try:
        if df is None or df.empty:
            return None

        df = clean_columns(df)
        if "Close" not in df.columns:
            return None

        close = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if len(close) < EMA_BEST + 30:
            return None

        ema21 = close.ewm(span=EMA_FAST, adjust=False).mean()
        ema50 = close.ewm(span=EMA_MID, adjust=False).mean()
        ema100 = close.ewm(span=EMA_BASE, adjust=False).mean()
        ema200 = close.ewm(span=EMA_BEST, adjust=False).mean()

        # Required crossovers.
        up21_100 = cross_up(ema21, ema100)
        up50_100 = cross_up(ema50, ema100)
        down21_100 = cross_down(ema21, ema100)
        down50_100 = cross_down(ema50, ema100)

        up100_200 = cross_up(ema100, ema200)
        down100_200 = cross_down(ema100, ema200)

        b21_i, b21_age = latest_cross_info(up21_100)
        b50_i, b50_age = latest_cross_info(up50_100)
        s21_i, s21_age = latest_cross_info(down21_100)
        s50_i, s50_age = latest_cross_info(down50_100)
        b200_i, b200_age = latest_cross_info(up100_200)
        s200_i, s200_age = latest_cross_info(down100_200)

        # CORE:
        # both 21 and 50 must cross 100 in the same direction and close
        # to one another. Both must still be fresh.
        core_buy = (
            b21_i is not None
            and b50_i is not None
            and abs(b21_i - b50_i) <= core_gap
            and max(b21_age, b50_age) <= core_validity
        )
        core_sell = (
            s21_i is not None
            and s50_i is not None
            and abs(s21_i - s50_i) <= core_gap
            and max(s21_age, s50_age) <= core_validity
        )

        # BEST:
        # 100/200 confirmation can happen BEFORE or AFTER the core setup.
        # This matches the user's idea that a 200 EMA crossover is the best
        # confirmation, without forcing it onto the exact same candle.
        core_buy_i = max(b21_i, b50_i) if core_buy else None
        core_sell_i = max(s21_i, s50_i) if core_sell else None

        best_buy = (
            core_buy
            and b200_i is not None
            and abs(b200_i - core_buy_i) <= best_window
        )
        best_sell = (
            core_sell
            and s200_i is not None
            and abs(s200_i - core_sell_i) <= best_window
        )

        # Current structure is useful confirmation/context.
        current_bull = ema21.iloc[-1] > ema50.iloc[-1] > ema100.iloc[-1] > ema200.iloc[-1]
        current_bear = ema21.iloc[-1] < ema50.iloc[-1] < ema100.iloc[-1] < ema200.iloc[-1]

        if best_buy:
            signal = "STRONG BUY"
            rank = 1
            core_index = core_buy_i
            core_age = max(b21_age, b50_age)
            best_age = b200_age
        elif core_buy:
            signal = "BUY"
            rank = 2
            core_index = core_buy_i
            core_age = max(b21_age, b50_age)
            best_age = np.nan
        elif best_sell:
            signal = "STRONG SELL"
            rank = 3
            core_index = core_sell_i
            core_age = max(s21_age, s50_age)
            best_age = s200_age
        elif core_sell:
            signal = "SELL"
            rank = 4
            core_index = core_sell_i
            core_age = max(s21_age, s50_age)
            best_age = np.nan
        else:
            # WATCH only if one side of the core crossover is fresh.
            partial_buy = (
                (
                    (b21_i is not None and b21_age <= core_validity)
                    or (b50_i is not None and b50_age <= core_validity)
                )
                and not core_buy
            )
            partial_sell = (
                (
                    (s21_i is not None and s21_age <= core_validity)
                    or (s50_i is not None and s50_age <= core_validity)
                )
                and not core_sell
            )

            if partial_buy or partial_sell:
                signal = "WATCH"
                rank = 5
            else:
                signal = "NO SIGNAL"
                rank = 6

            core_index = None
            core_age = np.nan
            best_age = np.nan

        close_now = float(close.iloc[-1])

        # Informational risk levels; signals themselves are crossover-based.
        if "BUY" in signal:
            stop = min(float(ema100.iloc[-1]), float(ema200.iloc[-1]))
            if stop >= close_now:
                stop = close_now * 0.98
            risk = max(close_now - stop, close_now * 0.01)
            target1 = close_now + risk * 1.5
            target2 = close_now + risk * 2.5
        elif "SELL" in signal:
            stop = max(float(ema100.iloc[-1]), float(ema200.iloc[-1]))
            if stop <= close_now:
                stop = close_now * 1.02
            risk = max(stop - close_now, close_now * 0.01)
            target1 = close_now - risk * 1.5
            target2 = close_now - risk * 2.5
        else:
            stop = np.nan
            target1 = np.nan
            target2 = np.nan

        crossover_date = None
        if core_index is not None:
            crossover_date = close.index[core_index]

        return {
            "Ticker": symbol.replace(".NS", ""),
            "Price": close_now,
            "EMA21": float(ema21.iloc[-1]),
            "EMA50": float(ema50.iloc[-1]),
            "EMA100": float(ema100.iloc[-1]),
            "EMA200": float(ema200.iloc[-1]),
            "21×100": "BULL" if (b21_i is not None and b21_age <= core_validity)
                       else ("BEAR" if (s21_i is not None and s21_age <= core_validity) else "NO"),
            "50×100": "BULL" if (b50_i is not None and b50_age <= core_validity)
                       else ("BEAR" if (s50_i is not None and s50_age <= core_validity) else "NO"),
            "100×200": "BULL" if (b200_i is not None and b200_age <= best_window)
                        else ("BEAR" if (s200_i is not None and s200_age <= best_window) else "NO"),
            "Core Age": core_age,
            "200 Age": best_age,
            "EMA Structure": (
                "21>50>100>200" if current_bull
                else ("21<50<100<200" if current_bear else "MIXED")
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
        }

    except Exception:
        return None


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def load_nse_equity_symbols():
    """
    Load the NSE equity universe robustly.

    Priority:
      1) NSE archive CSV
      2) NSE www CSV
      3) legacy www1 NSE CSV
      4) CSV link discovered from NSE's current securities page
      5) public mirror as a last resort

    A Session is used because NSE may require a warmed browser-like session
    and cookies before allowing the CSV request.
    """
    errors = []
    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "text/csv,text/plain,*/*;q=0.8",
        "Connection": "keep-alive",
    })

    def parse_equity_csv(content):
        df = pd.read_csv(io.BytesIO(content))
        df.columns = [str(c).strip().upper() for c in df.columns]

        if "SYMBOL" not in df.columns:
            raise ValueError("Downloaded file does not contain SYMBOL column.")

        if "SERIES" in df.columns:
            series = df["SERIES"].astype(str).str.strip().str.upper()
            df = df[series.eq("EQ")]

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

        symbols = [
            s for s in symbols
            if s not in {"SYMBOL", "UNDEFINED", "NAN"}
            and len(s) <= 40
            and " " not in s
        ]

        if len(symbols) < 500:
            raise ValueError(
                f"Universe looks incomplete ({len(symbols)} symbols)."
            )

        return sorted(symbols)

    def try_get(url, referer="https://www.nseindia.com/"):
        r = session.get(
            url,
            headers={"Referer": referer},
            timeout=30,
            allow_redirects=True,
        )
        r.raise_for_status()
        return r.content

    # Warm NSE session first. This often fixes 403s on cloud deployments.
    try:
        session.get(
            "https://www.nseindia.com/",
            headers={"Referer": "https://www.google.com/"},
            timeout=20,
            allow_redirects=True,
        )
        time.sleep(0.5)
    except Exception as e:
        errors.append(f"NSE session warm-up: {e}")

    # Try the known official CSV endpoints.
    for url in NSE_EQUITY_URLS:
        try:
            return parse_equity_csv(try_get(url))
        except Exception as e:
            errors.append(f"{url}: {e}")

    # Ask the current NSE securities page for the CSV href.
    try:
        page = session.get(
            NSE_SECURITY_PAGE,
            headers={"Referer": "https://www.nseindia.com/"},
            timeout=30,
            allow_redirects=True,
        )
        page.raise_for_status()

        import re
        hrefs = re.findall(
            r'''(?:href|src)\s*=\s*["']([^"']+EQUITY_L\.csv[^"']*)["']''',
            page.text,
            flags=re.IGNORECASE,
        )

        for href in hrefs:
            if href.startswith("/"):
                href = "https://www.nseindia.com" + href
            elif href.startswith("//"):
                href = "https:" + href
            elif not href.startswith("http"):
                href = "https://www.nseindia.com/" + href.lstrip("/")

            try:
                return parse_equity_csv(
                    try_get(href, referer=NSE_SECURITY_PAGE)
                )
            except Exception as e:
                errors.append(f"Discovered NSE CSV {href}: {e}")
    except Exception as e:
        errors.append(f"NSE securities page: {e}")

    # Last resort: public mirror.
    for url in NSE_MIRROR_URLS:
        try:
            r = requests.get(
                url,
                headers={"User-Agent": HEADERS["User-Agent"]},
                timeout=30,
                allow_redirects=True,
            )
            r.raise_for_status()
            return parse_equity_csv(r.content)
        except Exception as e:
            errors.append(f"Mirror {url}: {e}")

    raise RuntimeError(
        "All NSE universe sources failed. "
        "The Streamlit Cloud IP may be temporarily blocked by NSE. "
        "Details: " + " | ".join(errors[-6:])
    )


def download_batch(symbols):
    tickers = [s + ".NS" for s in symbols]
    try:
        return yf.download(
            tickers=tickers,
            period=YF_PERIOD,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="ticker",
        )
    except Exception:
        return None


def extract_close(data, ticker):
    if data is None or data.empty:
        return None

    try:
        if isinstance(data.columns, pd.MultiIndex):
            levels0 = list(data.columns.get_level_values(0))
            levels1 = list(data.columns.get_level_values(1))

            # yfinance group_by="ticker": (ticker, field)
            if ticker in levels0:
                part = data[ticker]
                if "Close" in part.columns:
                    return part[["Close"]].dropna()

            # Alternate layout: (field, ticker)
            if "Close" in levels0 and ticker in levels1:
                return pd.DataFrame({"Close": data["Close"][ticker]}).dropna()

        if "Close" in data.columns:
            return data[["Close"]].dropna()
    except Exception:
        return None

    return None


def run_scan(symbols, core_gap, core_validity, best_window):
    results = []
    total = len(symbols)

    progress = st.progress(0, text="Starting NSE scan...")
    status = st.empty()

    batches = [
        symbols[i:i + BATCH_SIZE]
        for i in range(0, len(symbols), BATCH_SIZE)
    ]

    for batch_no, batch in enumerate(batches, start=1):
        status.info(
            f"Downloading batch {batch_no}/{len(batches)} "
            f"• {len(batch)} stocks"
        )

        data = download_batch(batch)

        if data is not None and not data.empty:
            # Analysis is local/CPU work; using a few workers keeps UI responsive.
            with ThreadPoolExecutor(max_workers=6) as pool:
                futures = {}
                for symbol in batch:
                    ticker = symbol + ".NS"
                    close_df = extract_close(data, ticker)
                    futures[pool.submit(
                        analyze_symbol,
                        ticker,
                        close_df,
                        core_gap,
                        core_validity,
                        best_window,
                    )] = symbol

                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        results.append(result)

        done = min(batch_no * BATCH_SIZE, total)
        progress.progress(
            done / max(total, 1),
            text=f"Processed {done}/{total} stocks",
        )
        time.sleep(0.15)

    progress.empty()
    status.empty()

    return pd.DataFrame(results)


# ============================================================
# UI
# ============================================================

st.title("📈 Vardha EMA Crossover Screener V3")
st.caption(
    "NSE equity universe • Daily (1D) • EMA 21 / 50 / 100 / 200 • "
    "Core crossover + 200 EMA best confirmation"
)

with st.sidebar:
    st.header("⚙️ Strategy Settings")

    core_gap = st.slider(
        "21/50 crossover gap",
        min_value=1,
        max_value=10,
        value=5,
        help="EMA21 and EMA50 must cross EMA100 within this many trading sessions.",
    )

    core_validity = st.slider(
        "Core signal validity",
        min_value=3,
        max_value=30,
        value=15,
        help="A completed 21/50→100 setup remains a signal for this many daily candles.",
    )

    best_window = st.slider(
        "100/200 best confirmation window",
        min_value=5,
        max_value=40,
        value=20,
        help="100/200 crossover can occur before or after the core setup within this many sessions.",
    )

    st.markdown("---")
    st.write("**BUY:** 21 EMA ↑ 100 + 50 EMA ↑ 100")
    st.write("**SELL:** 21 EMA ↓ 100 + 50 EMA ↓ 100")
    st.write("**STRONG:** core + 100/200 confirmation")
    st.markdown("---")

    show_watch = st.checkbox("Show WATCH setups", value=True)
    show_no_signal = st.checkbox("Show NO SIGNAL stocks", value=False)

    if st.button("🧹 Clear NSE cache"):
        load_nse_equity_symbols.clear()
        st.rerun()

try:
    symbols = load_nse_equity_symbols()
except Exception as e:
    st.error(f"NSE universe load failed: {e}")
    st.info("Multiple NSE routes were tried. If NSE was temporarily blocking the cloud IP, click Clear NSE cache and rerun once.")
    st.stop()

if not symbols:
    st.error("No NSE equity symbols were loaded.")
    st.stop()

st.info(
    f"**NSE Equity universe loaded: {len(symbols)} symbols.** "
    "The scanner uses the NSE equity security list and scans the complete universe by default."
)

if "scan_results" not in st.session_state:
    st.session_state.scan_results = None

if st.button("🚀 SCAN ALL NSE STOCKS", type="primary", use_container_width=True):
    with st.spinner("Scanning 1D EMA strategy across NSE..."):
        st.session_state.scan_results = run_scan(
            symbols,
            core_gap,
            core_validity,
            best_window,
        )

df = st.session_state.scan_results

if df is None:
    st.warning("Click **SCAN ALL NSE STOCKS** to start.")
    st.stop()

if df.empty:
    st.warning(
        "No valid Yahoo Finance data was returned. "
        "Wait a little and scan again; this can happen during a data-provider rate limit."
    )
    st.stop()

strong_buy = int((df["Signal"] == "STRONG BUY").sum())
buy = int((df["Signal"] == "BUY").sum())
strong_sell = int((df["Signal"] == "STRONG SELL").sum())
sell = int((df["Signal"] == "SELL").sum())
watch = int((df["Signal"] == "WATCH").sum())

display_df = df.copy()

if not show_no_signal:
    display_df = display_df[display_df["Signal"] != "NO SIGNAL"]

if not show_watch:
    display_df = display_df[display_df["Signal"] != "WATCH"]

display_df = display_df.sort_values(
    by=["_rank", "Core Age", "Ticker"],
    ascending=[True, True, True],
    na_position="last",
)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Stocks Scanned", len(symbols))
c2.metric("🔥 Strong BUY", strong_buy)
c3.metric("🟢 BUY", buy)
c4.metric("🔥 Strong SELL", strong_sell)
c5.metric("🔴 SELL", sell)
c6.metric("👀 WATCH", watch)

st.markdown("### 🎯 EMA Strategy Signals")

if display_df.empty:
    st.success("No fresh EMA crossover setup found.")
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
        "100×200",
        "EMA Structure",
        "Core Age",
        "200 Age",
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
            "Core Age": st.column_config.NumberColumn(format="%.0f"),
            "200 Age": st.column_config.NumberColumn(format="%.0f"),
            "Stop Loss": st.column_config.NumberColumn(format="%.2f"),
            "Target 1": st.column_config.NumberColumn(format="%.2f"),
            "Target 2": st.column_config.NumberColumn(format="%.2f"),
        },
    )

st.markdown("### 📌 Final Strategy Rule")
st.write(
    f"""
    **Timeframe:** 1D

    **Core BUY:** EMA 21 and EMA 50 both cross above EMA 100, with the
    two crosses no more than **{core_gap} sessions** apart and the setup
    no older than **{core_validity} sessions**.

    **Core SELL:** exact opposite.

    **STRONG BUY/SELL:** the core setup plus EMA 100 crossing EMA 200 in
    the same direction within **{best_window} sessions before or after**
    the core crossover. The 100/200 crossover does not need to occur on
    the same candle.

    **WATCH:** only a fresh partial 21/50→100 crossover. Broad/random
    watchlist stocks are excluded.
    """
)

csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Current Signals CSV",
    data=csv,
    file_name="vardha_ema_final_signals.csv",
    mime="text/csv",
)

st.caption(
    "Educational/research tool — not investment advice. "
    "Signals depend on the latest available daily market data."
)
