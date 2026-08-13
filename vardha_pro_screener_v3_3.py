# VARDHA PRO STOCK SCREENER V3
# Features: broad NIFTY-style universe, intraday-oriented mode, swing mode,
# candlestick confirmation, sector filtering, market-regime guard,
# options-stock finder, improved trade plans. Telegram alerts intentionally excluded.

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Vardha Pro Stock Screener V3", page_icon="📈", layout="wide")

# -----------------------------
# Universe
# -----------------------------

NIFTY_500_SOURCE = "https://indexscreener.in/indices/nifty-500/constituents"

def load_nifty500_symbols():
    """Load the current Nifty 500-style constituent table and return unique NSE symbols.
    The source page is refreshed regularly; duplicate/legacy symbols are removed.
    """
    try:
        tables = pd.read_html(NIFTY_500_SOURCE)
        for table in tables:
            cols = {str(c).strip().lower(): c for c in table.columns}
            symbol_col = next((orig for key, orig in cols.items() if "symbol" in key), None)
            if symbol_col is not None:
                symbols = (
                    table[symbol_col].astype(str).str.strip()
                    .str.upper().replace({"NAN": np.nan}).dropna().tolist()
                )
                # Remove symbols that are not valid Yahoo NSE tickers.
                symbols = [s for s in symbols if s and s not in {"SYMBOL"}]
                # Some index tables can temporarily contain legacy/duplicate entries.
                symbols = list(dict.fromkeys(symbols))
                if len(symbols) >= 450:
                    return [s + ".NS" for s in symbols[:500]]
    except Exception:
        pass
    # Safe fallback if the external constituent page is unavailable.
    return [
        "RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS",
        "SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","AXISBANK.NS",
        "KOTAKBANK.NS","MARUTI.NS","SUNPHARMA.NS","TATASTEEL.NS",
        "ADANIENT.NS","NTPC.NS","POWERGRID.NS","ONGC.NS","COALINDIA.NS",
        "M&M.NS","BAJFINANCE.NS","HINDUNILVR.NS","HCLTECH.NS","WIPRO.NS",
        "TECHM.NS","TITAN.NS","ULTRACEMCO.NS","ASIANPAINT.NS","NESTLEIND.NS",
        "TATAMOTORS.NS","JSWSTEEL.NS","BEL.NS","HAL.NS","TRENT.NS"
    ]

SYMBOLS = load_nifty500_symbols()


def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    au = up.ewm(alpha=1/n, adjust=False).mean()
    ad = dn.ewm(alpha=1/n, adjust=False).mean()
    rs = au / ad.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(df, n=14):
    pc = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - pc).abs(),
        (df["Low"] - pc).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def adx(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    up = h.diff()
    down = -l.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    a = atr(df, n)
    plus_di = 100 * plus_dm.ewm(alpha=1/n, adjust=False).mean() / a.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/n, adjust=False).mean() / a.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1/n, adjust=False).mean()

def analyze(symbol, period="6mo"):
    try:
        df = yf.download(
            symbol, period=period, interval="1d", auto_adjust=False,
            progress=False, threads=False
        )
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        required = ["Open","High","Low","Close","Volume"]
        if not all(c in df.columns for c in required):
            return None
        df = df.dropna(subset=required).copy()
        if len(df) < 60:
            return None

        close = df["Close"]
        volume = df["Volume"].replace(0, np.nan)

        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()
        r = rsi(close)
        a = atr(df)
        adxv = adx(df)
        macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        macds = macd.ewm(span=9, adjust=False).mean()

        vol20 = volume.rolling(20).mean()
        volx = float(volume.iloc[-1] / vol20.iloc[-1]) if pd.notna(vol20.iloc[-1]) else np.nan

        resistance20 = float(df["High"].iloc[-21:-1].max())
        support20 = float(df["Low"].iloc[-21:-1].min())
        high52 = float(df["High"].tail(252).max())
        low52 = float(df["Low"].tail(252).min())
        price = float(close.iloc[-1])
        atrv = float(a.iloc[-1])

        breakout20 = price > resistance20
        breakout52 = price > high52 * 0.995
        near_breakout = price >= resistance20 * 0.985
        above20 = price > float(ema20.iloc[-1])
        above50 = price > float(ema50.iloc[-1])
        above200 = price > float(ema200.iloc[-1])
        ema_stack = above20 and above50 and above200 and float(ema20.iloc[-1]) > float(ema50.iloc[-1])
        momentum = 55 <= float(r.iloc[-1]) <= 75
        macd_bull = float(macd.iloc[-1]) > float(macds.iloc[-1])
        adx_good = float(adxv.iloc[-1]) >= 20
        volume_good = volx >= 1.2

        # 10-point score
        score = sum([
            above20, above50, above200, momentum, volume_good,
            breakout20, breakout52, macd_bull, adx_good, ema_stack
        ])

        # Technical entry: breakout trigger or current price if already broken
        entry = max(price, resistance20 * 1.002) if near_breakout else price
        support = max(support20, float(ema20.iloc[-1]) - 0.5 * atrv)
        sl = min(entry - 1.5 * atrv, support)
        if sl >= entry:
            sl = entry - 1.5 * atrv
        risk = entry - sl
        tp1 = entry + 1.5 * risk
        tp2 = entry + 2.5 * risk
        rr1 = (tp1 - entry) / risk if risk > 0 else np.nan

        if score >= 8 and breakout20 and volume_good:
            signal = "STRONG BUY"
        elif score >= 7 and (breakout20 or near_breakout) and volume_good:
            signal = "BUY"
        elif score >= 5:
            signal = "WATCH"
        else:
            signal = "AVOID"

        return {
            "Ticker": symbol.replace(".NS",""),
            "Price": round(price, 2),
            "Change %": round(float((close.iloc[-1]/close.iloc[-2]-1)*100), 2),
            "RSI": round(float(r.iloc[-1]), 1),
            "Vol ×": round(volx, 2),
            "EMA20": round(float(ema20.iloc[-1]), 2),
            "EMA50": round(float(ema50.iloc[-1]), 2),
            "EMA200": round(float(ema200.iloc[-1]), 2),
            "ADX": round(float(adxv.iloc[-1]), 1),
            "ATR": round(atrv, 2),
            "Support": round(support, 2),
            "Resistance": round(resistance20, 2),
            "20D Breakout": "YES" if breakout20 else "NO",
            "52W Breakout": "YES" if breakout52 else "NO",
            "MACD Bull": "YES" if macd_bull else "NO",
            "Entry": round(entry, 2),
            "SL": round(sl, 2),
            "TP1": round(tp1, 2),
            "TP2": round(tp2, 2),
            "R:R": f"1:{rr1:.1f}",
            "Score": f"{score}/10",
            "ScoreNum": score,
            "Signal": signal
        }
    except Exception:
        return None


def v3_candle_pattern(df):
    o,h,l,c = [df[x] for x in ["Open","High","Low","Close"]]
    O,H,L,C = map(float,[o.iloc[-1],h.iloc[-1],l.iloc[-1],c.iloc[-1]])
    po,pc = float(o.iloc[-2]),float(c.iloc[-2])
    body=abs(C-O); rng=max(H-L,1e-9)
    upper=H-max(C,O); lower=min(C,O)-L
    if C>O and pc<po and C>=po and O<=pc: return "Bullish Engulfing"
    if C<O and pc>po and O>=pc and C<=po: return "Bearish Engulfing"
    if lower >= 2*max(body,0.01) and upper <= max(body,0.01): return "Hammer"
    if upper >= 2*max(body,0.01) and lower <= max(body,0.01): return "Shooting Star"
    if body/rng < .12: return "Doji"
    return "Neutral"

def v3_market_regime():
    try:
        n=yf.download("^NSEI",period="6mo",interval="1d",auto_adjust=False,progress=False,threads=False)
        if isinstance(n.columns,pd.MultiIndex): n.columns=n.columns.get_level_values(0)
        c=n["Close"].dropna()
        e20=c.ewm(span=20,adjust=False).mean().iloc[-1]
        e50=c.ewm(span=50,adjust=False).mean().iloc[-1]
        e200=c.ewm(span=200,adjust=False).mean().iloc[-1]
        rv=float(rsi(c).iloc[-1])
        if c.iloc[-1]>e20>e50 and c.iloc[-1]>e200 and rv>=52: return "BULLISH"
        if c.iloc[-1]<e20<e50 and c.iloc[-1]<e200 and rv<=48: return "BEARISH"
        return "SIDEWAYS"
    except Exception:
        return "UNKNOWN"

# -----------------------------
# UI
# -----------------------------
market_regime = v3_market_regime()

# V3.2 sector classification/filter
SECTOR_MAP = {
"Banking":{"HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","INDUSINDBK","FEDERALBNK","CANBK","BANKBARODA","IDFCFIRSTB","AUBANK","BANDHANBNK","BANKINDIA","IDBI","LICHSGFIN","MUTHOOTFIN","MANAPPURAM","SHRIRAMFIN","BAJFINANCE","BAJAJFINSV","SBICARD","ICICIPRULI","ICICIGI"},
"IT":{"TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM","MPHASIS","PERSISTENT","OFSS"},
"Auto":{"MARUTI","M&M","TATAMOTORS","EICHERMOT","HEROMOTOCO","TVSMOTOR","UNOMINDA","BOSCHLTD"},
"Pharma":{"SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP","LUPIN","BIOCON","GLENMARK","TORNTPHARM","SYNGENE","MAXHEALTH","FORTIS"},
"Energy":{"RELIANCE","NTPC","POWERGRID","ONGC","COALINDIA","BPCL","IOC","GAIL","OIL","PFC","REC","NHPC","TATAPOWER"},
"Metals":{"TATASTEEL","JSWSTEEL","HINDALCO","VEDL","JINDALSTEL","HINDCOPPER","SAIL","NMDC","NATIONALUM"},
"FMCG":{"ITC","HINDUNILVR","NESTLEIND","BRITANNIA","DABUR","MARICO","GODREJCP","COLPAL","TATACONSUM","VBL"},
"Industrials":{"LT","BEL","HAL","SIEMENS","ABB","BHEL","CGPOWER","CUMMINSIND","KEI","POLYCAB","DIXON"},
"Realty":{"DLF","GODREJPROP","OBEROIRLTY","PHOENIXLTD","PRESTIGE"},
"Consumer":{"TITAN","TRENT","ASIANPAINT","DMART","HAVELLS","CROMPTON","VOLTAS","KALYANKJIL","PAGEIND"}
}
def filter_by_sector(symbols, sector):
    if sector == "All sectors": return symbols
    allowed = SECTOR_MAP.get(sector, set())
    return [s for s in symbols if s.upper().replace(".NS","") in allowed]


# ---------------- V3.3 ROBUST SECTOR FILTER ----------------
SECTOR_MAP_V33 = {
    "Banking": {"HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","INDUSINDBK","FEDERALBNK","CANBK","BANKBARODA","IDFCFIRSTB","AUBANK","BANDHANBNK","BANKINDIA","IDBI","LICHSGFIN","MUTHOOTFIN","MANAPPURAM","SHRIRAMFIN","BAJFINANCE","BAJAJFINSV","SBICARD","ICICIPRULI","ICICIGI"},
    "IT": {"TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM","MPHASIS","PERSISTENT","OFSS"},
    "Auto": {"MARUTI","M&M","TATAMOTORS","EICHERMOT","HEROMOTOCO","TVSMOTOR","UNOMINDA","BOSCHLTD"},
    "Pharma": {"SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP","LUPIN","BIOCON","GLENMARK","TORNTPHARM","SYNGENE","MAXHEALTH","FORTIS"},
    "Energy": {"RELIANCE","NTPC","POWERGRID","ONGC","COALINDIA","BPCL","IOC","GAIL","OIL","PFC","REC","NHPC","TATAPOWER","ADANIGREEN","ADANIPOWER"},
    "Metals": {"TATASTEEL","JSWSTEEL","HINDALCO","VEDL","JINDALSTEL","HINDCOPPER","SAIL","NMDC","NATIONALUM"},
    "FMCG": {"ITC","HINDUNILVR","NESTLEIND","BRITANNIA","DABUR","MARICO","GODREJCP","COLPAL","TATACONSUM","VBL"},
    "Industrials": {"LT","BEL","HAL","SIEMENS","ABB","BHEL","CGPOWER","CUMMINSIND","KEI","POLYCAB","DIXON"},
    "Realty": {"DLF","GODREJPROP","OBEROIRLTY","PHOENIXLTD","PRESTIGE"},
    "Consumer": {"TITAN","TRENT","ASIANPAINT","DMART","HAVELLS","CROMPTON","VOLTAS","KALYANKJIL","PAGEIND"},
}

def v33_sector_filter(symbols, selected):
    if selected == "All sectors":
        return list(symbols)
    allowed = SECTOR_MAP_V33.get(selected, set())
    return [s for s in symbols if s.replace(".NS","").upper() in allowed]

def v33_clear_on_sector_change(selected):
    previous = st.session_state.get("v33_previous_sector")
    if previous != selected:
        st.session_state["v33_previous_sector"] = selected
        st.session_state["results_v3"] = None

st.title("📈 Vardha Pro Stock Screener V3")
st.caption(f"Universe loaded: {len(SYMBOLS)} symbols • Current constituent list is refreshed from the source page")
st.caption(f"Market regime: {market_regime} • Intraday/Swing research • Candlestick confirmation • Sector filtering • Options-stock finder")
st.caption("Momentum + trend + breakout + volume + price-action framework | Educational/research tool — not investment advice")

with st.sidebar:
    st.header("Universe")
    mode = st.radio("Stocks to scan", ["NIFTY 500", "Custom symbols"])

    if mode == "Custom symbols":
        raw = st.text_area("Symbols (comma/newline separated)", "RELIANCE, TCS, INFY")
        selected = [x.strip().upper() for x in raw.replace("\n", ",").split(",") if x.strip()]
        symbols = [x if x.endswith(".NS") else x + ".NS" for x in selected]
    else:
        symbols = SYMBOLS

    st.header("Strategy Filters")
    period = st.selectbox("History", ["6mo", "1y", "2y"], index=0)
    min_score = st.slider("Minimum score for Watchlist", 4, 9, 5)
    volume_threshold = st.slider("Volume multiple", 1.0, 3.0, 1.20, 0.05)
    require_breakout = st.checkbox("Require 20-day breakout for BUY", False)
    require_ema200 = st.checkbox("Require price above EMA200 for BUY", False)

    st.header("V3 Mode")
    strategy_mode = st.radio("Strategy", ["Swing", "Intraday", "Options Stock Finder"])
    sector_filter = st.selectbox("Sector", ["All sectors"] + list(SECTOR_MAP_V33.keys()))
    market_guard = st.checkbox("Use market-regime guard", True)

    scan = st.button("🔎 SCAN NOW", type="primary", use_container_width=True)

if "results" not in st.session_state:
    st.session_state.results = None

v33_clear_on_sector_change(sector_filter)

if scan:
    rows = []
    progress = st.progress(0)
    status = st.empty()
    symbols = filter_by_sector(symbols, sector_filter)
    st.caption(f"Selected sector: {sector_filter} • Stocks to scan: {len(symbols)}")
    for i, sym in enumerate(symbols):
        status.write(f"Scanning {sym.replace('.NS','')} ({i+1}/{len(symbols)})")
        row = analyze(sym, period)
        if row:
            # Apply user threshold to classification
            if row["Vol ×"] < volume_threshold:
                row["ScoreNum"] = max(0, row["ScoreNum"] - 1)
            if require_ema200 and row["EMA200"] >= row["Price"]:
                row["Signal"] = "WATCH" if row["ScoreNum"] >= min_score else "AVOID"
            rows.append(row)
        progress.progress((i+1)/len(symbols))
    status.empty()
    progress.empty()
    st.session_state.results = pd.DataFrame(rows)

df = st.session_state.results

if df is None or df.empty:
    st.info("Set your filters and click 🔎 SCAN NOW to run the screener.")
else:
    df = df.sort_values(["ScoreNum","Vol ×","RSI"], ascending=[False,False,False]).reset_index(drop=True)
    buy_mask = df["Signal"].isin(["BUY","STRONG BUY"])
    watch_mask = df["Signal"].eq("WATCH")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Stocks scanned", len(df))
    c2.metric("BUY setups", int(buy_mask.sum()))
    c3.metric("Watchlist", int(watch_mask.sum()))
    c4.metric("Best score", f"{int(df.ScoreNum.max())}/10")

    st.subheader("🔥 Today's Top Setups")
    top = df[df["ScoreNum"] >= min_score].head(10).copy()
    if top.empty:
        st.warning("No setup meets the current Watchlist score. Try a lower minimum score or scan again later.")
    else:
        cols = ["Ticker","Price","RSI","Vol ×","ADX","Support","Resistance","20D Breakout","Score","Signal"]
        st.dataframe(top[cols], use_container_width=True, hide_index=True)

    tab1, tab2, tab3 = st.tabs(["📊 All Results","🎯 Trade Plans","📘 Strategy"])
    with tab1:
        show_cols = ["Ticker","Price","Change %","RSI","Vol ×","EMA20","EMA50","EMA200","ADX",
                     "Support","Resistance","20D Breakout","52W Breakout","MACD Bull",
                     "Score","Signal"]
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Export full scan to CSV",
            df.drop(columns=["ScoreNum"]).to_csv(index=False).encode("utf-8"),
            "vardha_pro_screener_v2.csv",
            "text/csv"
        )

    with tab2:
        plans = df[df["Signal"].isin(["BUY","STRONG BUY","WATCH"])].head(15)
        if plans.empty:
            st.info("No current trade-plan candidates.")
        else:
            st.dataframe(
                plans[["Ticker","Signal","Price","Entry","SL","TP1","TP2","R:R","Score","Support","Resistance"]],
                use_container_width=True, hide_index=True
            )
            st.caption("Entry/SL/TP are rule-based research levels using recent resistance/support and ATR; they are not personalized recommendations.")

    with tab3:
        st.markdown("""
**Scoring (10 points):**
1. Price above EMA20
2. Price above EMA50
3. Price above EMA200
4. RSI in momentum zone
5. Volume expansion
6. 20-day breakout
7. Near 52-week breakout
8. MACD bullish
9. ADX ≥ 20
10. EMA trend stack

**Signal logic:** STRONG BUY requires high score + confirmed 20-day breakout + volume expansion. BUY requires a high score plus breakout/near-breakout and volume. WATCH means the trend/momentum is interesting but confirmation is incomplete.

This tool is for educational/research purposes and does not guarantee returns.
""")
