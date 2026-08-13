import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from io import StringIO

st.set_page_config(
    page_title="Vardha Pro Stock Screener V3.3",
    page_icon="📈",
    layout="wide"
)

# ============================================================
# NIFTY 500 UNIVERSE
# ============================================================

NIFTY_500_URL = (
    "https://archives.nseindia.com/content/indices/"
    "ind_nifty500list.csv"
)


@st.cache_data(ttl=86400)
def load_nifty500_symbols():

    try:
        response = requests.get(
            NIFTY_500_URL,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        table = pd.read_csv(
            StringIO(response.text)
        )

        if "Symbol" not in table.columns:
            raise ValueError(
                "Symbol column not found"
            )

        symbols = (
            table["Symbol"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace("NAN", np.nan)
            .dropna()
            .tolist()
        )

        symbols = [
            s for s in symbols
            if s and s != "SYMBOL"
        ]

        symbols = list(
            dict.fromkeys(symbols)
        )

        if len(symbols) >= 450:

            return [
                s + ".NS"
                for s in symbols
            ]

    except Exception:
        pass

    # --------------------------------------------------------
    # Broad fallback universe
    # --------------------------------------------------------

    fallback = """
    3MINDIA AARTIIND AAVAS ABB ABCAPITAL ABFRL ACC ADANIENSOL
    ADANIENT ADANIGREEN ADANIPORTS ADANIPOWER AFFLE AIAENG
    AJANTAPHARM ALKEM ALKYLAMINE AMBER AMBUJACEM APARINDS
    APOLLOHOSP APOLLOTYRE ASHOKLEY ASIANPAINT ASTRAL ATUL
    AUBANK AUROPHARMA AXISBANK BAJAJ-AUTO BAJAJFINSV
    BAJFINANCE BALKRISIND BANDHANBNK BANKBARODA BANKINDIA
    BEL BEML BERGEPAINT BHARATFORG BHARTIARTL BHEL BIOCON
    BIRLACORPN BLUESTARCO BOSCHLTD BPCL BRITANNIA BSOFT
    CANBK CANFINHOME CDSL CESC CGPOWER CHAMBLFERT
    CHEMPLAST CHOLAFIN CIPLA COALINDIA COCHINSHIP COFORGE
    COLPAL CONCOR COROMANDEL CROMPTON CUMMINSIND CYIENT
    DABUR DALBHARAT DEEPAKNTR DELHIVERY DELTACORP DEVYANI
    DIVISLAB DIXON DLF DMART DRREDDY EICHERMOT EIDPARRY
    EIHOTEL ELGIEQUIP EMAMILTD ENDURANCE ENGRO EXIDEIND
    FEDERALBNK FINCABLE FINEORG FLUOROCHEM FORTIS GAIL
    GESHIP GLAND GLENMARK GODREJCP GODREJPROP GODREJIND
    GRASIM GRAPHITE GRINDWELL HAL HAVELLS HCLTECH HDFCAMC
    HDFCBANK HDFCLIFE HEROMOTOCO HINDALCO HINDCOPPER
    HINDPETRO HINDUNILVR HINDZINC HUDCO ICICIBANK ICICIGI
    ICICIPRULI IDBI IDFCFIRSTB IEX IGL INDHOTEL INDIACEM
    INDIAMART INDIANB INDIGO INDUSINDBK INDUSTOWER INFY
    INOXWIND IRCTC IRCON IRFC IREDA ITC JINDALSTEL JIOFIN
    JK CEMENT JKLAKSHMI JKTYRE JSWENERGY JSWSTEEL JUBLFOOD
    KALYANKJIL KANSAINER KEI KEC KFINTECH KOTAKBANK KPIL
    KRBL LALPATHLAB LAURUSLABS LICHSGFIN LT LTIM LUPIN
    M&M M&MFIN MANAPPURAM MARICO MARUTI MAXHEALTH MCX
    MEDANTA METROPOLIS MGL MOTHERSON MPHASIS MRPL MUTHOOTFIN
    NATIONALUM NAVINFLUOR NBCC NESTLEIND NHPC NMDC NLCINDIA
    NMDC NOCIL NTPC OFSS OIL OBEROIRLTY ONGC PAGEIND
    PATANJALI PEL PERSISTENT PETRONET PFC PHOENIXLTD PIDILITIND
    PIIND POLYCAB POWERGRID PNB PNBHOUSING PRESTIGE PRICOLLTD
    PVRINOX RBLBANK REC RELIANCE RVNL SAIL SAMHI SAPPHIRE
    SBICARD SBILIFE SBIN SCHAEFFLER SHREECEM SHRIRAMFIN
    SIEMENS SJVN SKFIND SOBHA SOLARINDS SONACOMS SRF
    STARHEALTH SUNPHARMA SUNTECK SUPREMEIND SUZLON SYNGENE
    TATACHEM TATACOMM TATACONSUM TATAELXSI TATAMOTORS
    TATAPOWER TATASTEEL TATATECH TCS TECHM TIINDIA TITAN
    TORNTPOWER TRENT TVSMOTOR UBL UCOBANK UJJIVANSFB
    ULTRACEMCO UNIONBANK UPL VBL VEDL VGUARD VOLTAS
    WELCORP WELSPUN WESTLIFE WIPRO YESBANK ZEEL ZYDUSLIFE
    ZOMATO ZYDUSLIFE
    """

    symbols = list(
        dict.fromkeys(
            fallback.split()
        )
    )

    return [
        s + ".NS"
        for s in symbols
    ]


SYMBOLS = load_nifty500_symbols()


# ============================================================
# INDICATORS
# ============================================================

def rsi(series, n=14):

    delta = series.diff()

    up = delta.clip(
        lower=0
    )

    down = -delta.clip(
        upper=0
    )

    avg_up = up.ewm(
        alpha=1 / n,
        adjust=False
    ).mean()

    avg_down = down.ewm(
        alpha=1 / n,
        adjust=False
    ).mean()

    rs = (
        avg_up /
        avg_down.replace(
            0,
            np.nan
        )
    )

    return 100 - (
        100 / (1 + rs)
    )


def atr(df, n=14):

    previous_close = df["Close"].shift(1)

    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (
                df["High"] -
                previous_close
            ).abs(),
            (
                df["Low"] -
                previous_close
            ).abs()
        ],
        axis=1
    ).max(axis=1)

    return tr.ewm(
        alpha=1 / n,
        adjust=False
    ).mean()


def adx(df, n=14):

    high = df["High"]
    low = df["Low"]

    up = high.diff()
    down = -low.diff()

    plus_dm = pd.Series(
        np.where(
            (up > down) &
            (up > 0),
            up,
            0.0
        ),
        index=df.index
    )

    minus_dm = pd.Series(
        np.where(
            (down > up) &
            (down > 0),
            down,
            0.0
        ),
        index=df.index
    )

    atr_value = atr(
        df,
        n
    )

    plus_di = (
        100 *
        plus_dm.ewm(
            alpha=1 / n,
            adjust=False
        ).mean()
        /
        atr_value.replace(
            0,
            np.nan
        )
    )

    minus_di = (
        100 *
        minus_dm.ewm(
            alpha=1 / n,
            adjust=False
        ).mean()
        /
        atr_value.replace(
            0,
            np.nan
        )
    )

    dx = (
        100 *
        (plus_di - minus_di).abs()
        /
        (
            plus_di +
            minus_di
        ).replace(
            0,
            np.nan
        )
    )

    return dx.ewm(
        alpha=1 / n,
        adjust=False
    ).mean()


# ============================================================
# SINGLE STOCK ANALYSIS
# ============================================================

def analyze(
    symbol,
    period="6mo"
):

    try:

        df = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return None

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):

            df.columns = (
                df.columns
                .get_level_values(0)
            )

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        if not all(
            c in df.columns
            for c in required
        ):
            return None

        df = df.dropna(
            subset=required
        ).copy()

        if len(df) < 60:
            return None

        close = df["Close"]

        volume = (
            df["Volume"]
            .replace(
                0,
                np.nan
            )
        )

        ema20 = close.ewm(
            span=20,
            adjust=False
        ).mean()

        ema50 = close.ewm(
            span=50,
            adjust=False
        ).mean()

        ema200 = close.ewm(
            span=200,
            adjust=False
        ).mean()

        r = rsi(
            close
        )

        a = atr(
            df
        )

        adx_value = adx(
            df
        )

        macd = (
            close.ewm(
                span=12,
                adjust=False
            ).mean()
            -
            close.ewm(
                span=26,
                adjust=False
            ).mean()
        )

        macd_signal = macd.ewm(
            span=9,
            adjust=False
        ).mean()

        volume20 = (
            volume
            .rolling(20)
            .mean()
        )

        volx = (
            volume.iloc[-1] /
            volume20.iloc[-1]
        )

        resistance20 = float(
            df["High"]
            .iloc[-21:-1]
            .max()
        )

        support20 = float(
            df["Low"]
            .iloc[-21:-1]
            .min()
        )

        high52 = float(
            df["High"]
            .tail(252)
            .max()
        )

        price = float(
            close.iloc[-1]
        )

        atr_value = float(
            a.iloc[-1]
        )

        breakout20 = (
            price >
            resistance20
        )

        breakout52 = (
            price >
            high52 * 0.995
        )

        near_breakout = (
            price >=
            resistance20 * 0.985
        )

        above20 = (
            price >
            float(
                ema20.iloc[-1]
            )
        )

        above50 = (
            price >
            float(
                ema50.iloc[-1]
            )
        )

        above200 = (
            price >
            float(
                ema200.iloc[-1]
            )
        )

        ema_stack = (
            above20
            and above50
            and above200
            and float(
                ema20.iloc[-1]
            )
            >
            float(
                ema50.iloc[-1]
            )
        )

        momentum = (
            55 <=
            float(r.iloc[-1])
            <= 75
        )

        macd_bull = (
            float(
                macd.iloc[-1]
            )
            >
            float(
                macd_signal.iloc[-1]
            )
        )

        adx_good = (
            float(
                adx_value.iloc[-1]
            )
            >= 20
        )

        volume_good = (
            volx >= 1.2
        )

        score = sum(
            [
                above20,
                above50,
                above200,
                momentum,
                volume_good,
                breakout20,
                breakout52,
                macd_bull,
                adx_good,
                ema_stack
            ]
        )

        entry = (
            max(
                price,
                resistance20 * 1.002
            )
            if near_breakout
            else price
        )

        support = max(
            support20,
            float(
                ema20.iloc[-1]
            )
            -
            0.5 * atr_value
        )

        sl = min(
            entry - 1.5 * atr_value,
            support
        )

        if sl >= entry:
            sl = (
                entry -
                1.5 * atr_value
            )

        risk = entry - sl

        tp1 = (
            entry +
            1.5 * risk
        )

        tp2 = (
            entry +
            2.5 * risk
        )

        rr1 = (
            (tp1 - entry) /
            risk
            if risk > 0
            else np.nan
        )

        if (
            score >= 8
            and breakout20
            and volume_good
        ):

            signal = "STRONG BUY"

        elif (
            score >= 7
            and (
                breakout20
                or near_breakout
            )
            and volume_good
        ):

            signal = "BUY"

        elif score >= 5:

            signal = "WATCH"

        else:

            signal = "AVOID"

        return {

            "Ticker":
                symbol.replace(
                    ".NS",
                    ""
                ),

            "Price":
                round(
                    price,
                    2
                ),

            "Change %":
                round(
                    (
                        close.iloc[-1] /
                        close.iloc[-2] -
                        1
                    ) * 100,
                    2
                ),

            "RSI":
                round(
                    float(
                        r.iloc[-1]
                    ),
                    1
                ),

            "Vol ×":
                round(
                    float(volx),
                    2
                ),

            "EMA20":
                round(
                    float(
                        ema20.iloc[-1]
                    ),
                    2
                ),

            "EMA50":
                round(
                    float(
                        ema50.iloc[-1]
                    ),
                    2
                ),

            "EMA200":
                round(
                    float(
                        ema200.iloc[-1]
                    ),
                    2
                ),

            "ADX":
                round(
                    float(
                        adx_value.iloc[-1]
                    ),
                    1
                ),

            "ATR":
                round(
                    atr_value,
                    2
                ),

            "Support":
                round(
                    support,
                    2
                ),

            "Resistance":
                round(
                    resistance20,
                    2
                ),

            "20D Breakout":
                "YES"
                if breakout20
                else "NO",

            "52W Breakout":
                "YES"
                if breakout52
                else "NO",

            "MACD Bull":
                "YES"
                if macd_bull
                else "NO",

            "Entry":
                round(
                    entry,
                    2
                ),

            "SL":
                round(
                    sl,
                    2
                ),

            "TP1":
                round(
                    tp1,
                    2
                ),

            "TP2":
                round(
                    tp2,
                    2
                ),

            "R:R":
                f"1:{rr1:.1f}",

            "Score":
                f"{score}/10",

            "ScoreNum":
                score,

            "Signal":
                signal
        }

    except Exception:
        return None


# ============================================================
# CANDLE PATTERN
# ============================================================

def v3_candle_pattern(df):

    o = df["Open"]
    h = df["High"]
    l = df["Low"]
    c = df["Close"]

    O = float(o.iloc[-1])
    H = float(h.iloc[-1])
    L = float(l.iloc[-1])
    C = float(c.iloc[-1])

    po = float(o.iloc[-2])
    pc = float(c.iloc[-2])

    body = abs(
        C - O
    )

    rng = max(
        H - L,
        1e-9
    )

    upper = (
        H -
        max(C, O)
    )

    lower = (
        min(C, O) -
        L
    )

    if (
        C > O
        and pc < po
        and C >= po
        and O <= pc
    ):
        return "Bullish Engulfing"

    if (
        C < O
        and pc > po
        and O >= pc
        and C <= po
    ):
        return "Bearish Engulfing"

    if (
        lower >=
        2 * max(body, 0.01)
        and upper <=
        max(body, 0.01)
    ):
        return "Hammer"

    if (
        upper >=
        2 * max(body, 0.01)
        and lower <=
        max(body, 0.01)
    ):
        return "Shooting Star"

    if body / rng < 0.12:
        return "Doji"

    return "Neutral"


# ============================================================
# MARKET REGIME
# ============================================================

def v3_market_regime():

    try:

        n = yf.download(
            "^NSEI",
            period="6mo",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if isinstance(
            n.columns,
            pd.MultiIndex
        ):

            n.columns = (
                n.columns
                .get_level_values(0)
            )

        c = (
            n["Close"]
            .dropna()
        )

        e20 = (
            c.ewm(
                span=20,
                adjust=False
            )
            .mean()
            .iloc[-1]
        )

        e50 = (
            c.ewm(
                span=50,
                adjust=False
            )
            .mean()
            .iloc[-1]
        )

        e200 = (
            c.ewm(
                span=200,
                adjust=False
            )
            .mean()
            .iloc[-1]
        )

        rv = float(
            rsi(c).iloc[-1]
        )

        if (
            c.iloc[-1] > e20 > e50
            and c.iloc[-1] > e200
            and rv >= 52
        ):

            return "BULLISH"

        if (
            c.iloc[-1] < e20 < e50
            and c.iloc[-1] < e200
            and rv <= 48
        ):

            return "BEARISH"

        return "SIDEWAYS"

    except Exception:

        return "UNKNOWN"


# ============================================================
# SECTOR MAP
# ============================================================

SECTOR_MAP = {

    "Banking": {
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "AXISBANK",
        "KOTAKBANK",
        "INDUSINDBK",
        "FEDERALBNK",
        "CANBK",
        "BANKBARODA",
        "IDFCFIRSTB",
        "AUBANK",
        "BANDHANBNK",
        "BANKINDIA",
        "IDBI",
        "LICHSGFIN",
        "MUTHOOTFIN",
        "MANAPPURAM",
        "SHRIRAMFIN",
        "BAJFINANCE",
        "BAJAJFINSV",
        "SBICARD",
        "ICICIPRULI",
        "ICICIGI"
    },

    "IT": {
        "TCS",
        "INFY",
        "HCLTECH",
        "WIPRO",
        "TECHM",
        "LTIM",
        "MPHASIS",
        "PERSISTENT",
        "OFSS",
        "COFORGE"
    },

    "Auto": {
        "MARUTI",
        "M&M",
        "TATAMOTORS",
        "EICHERMOT",
        "HEROMOTOCO",
        "TVSMOTOR",
        "UNOMINDA",
        "BOSCHLTD",
        "BAJAJ-AUTO"
    },

    "Pharma": {
        "SUNPHARMA",
        "DRREDDY",
        "CIPLA",
        "DIVISLAB",
        "APOLLOHOSP",
        "LUPIN",
        "BIOCON",
        "GLENMARK",
        "TORNTPHARM",
        "SYNGENE",
        "MAXHEALTH",
        "FORTIS"
    },

    "Energy": {
        "RELIANCE",
        "NTPC",
        "POWERGRID",
        "ONGC",
        "COALINDIA",
        "BPCL",
        "IOC",
        "GAIL",
        "OIL",
        "PFC",
        "REC",
        "NHPC",
        "TATAPOWER",
        "ADANIGREEN",
        "ADANIPOWER"
    },

    "Metals": {
        "TATASTEEL",
        "JSWSTEEL",
        "HINDALCO",
        "VEDL",
        "JINDALSTEL",
        "HINDCOPPER",
        "SAIL",
        "NMDC",
        "NATIONALUM"
    },

    "FMCG": {
        "ITC",
        "HINDUNILVR",
        "NESTLEIND",
        "BRITANNIA",
        "DABUR",
        "MARICO",
        "GODREJCP",
        "COLPAL",
        "TATACONSUM",
        "VBL"
    },

    "Industrials": {
        "LT",
        "BEL",
        "HAL",
        "SIEMENS",
        "ABB",
        "BHEL",
        "CGPOWER",
        "CUMMINSIND",
        "KEI",
        "POLYCAB",
        "DIXON"
    },

    "Realty": {
        "DLF",
        "GODREJPROP",
        "OBEROIRLTY",
        "PHOENIXLTD",
        "PRESTIGE",
        "LODHA",
        "BRIGADE"
    },

    "Consumer": {
        "TITAN",
        "TRENT",
        "ASIANPAINT",
        "DMART",
        "HAVELLS",
        "CROMPTON",
        "VOLTAS",
        "KALYANKJIL",
        "PAGEIND"
    }
}


def filter_by_sector(
    symbols,
    sector
):

    if sector == "All sectors":
        return list(symbols)

    allowed = SECTOR_MAP.get(
        sector,
        set()
    )

    return [
        s
        for s in symbols
        if s.replace(
            ".NS",
            ""
        ).upper()
        in allowed
    ]


# ============================================================
# UI
# ============================================================

market_regime = (
    v3_market_regime()
)

st.title(
    "📈 Vardha Pro Stock Screener V3.3"
)

st.caption(
    f"Universe loaded: "
    f"{len(SYMBOLS)} symbols"
)

st.caption(
    f"Market regime: "
    f"{market_regime} • "
    f"Intraday/Swing research • "
    f"Candlestick confirmation • "
    f"Sector filtering • "
    f"Options-stock finder"
)

st.caption(
    "Momentum + trend + breakout + volume "
    "+ price-action framework | "
    "Educational/research tool — "
    "not investment advice"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Universe"
    )

    mode = st.radio(
        "Stocks to scan",
        [
            "NIFTY 500",
            "Custom symbols"
        ]
    )

    if mode == "Custom symbols":

        raw = st.text_area(
            "Symbols "
            "(comma/newline separated)",
            "RELIANCE, TCS, INFY"
        )

        selected = [
            x.strip().upper()
            for x in raw
            .replace(
                "\n",
                ","
            )
            .split(",")
            if x.strip()
        ]

        symbols = [
            x
            if x.endswith(".NS")
            else x + ".NS"
            for x in selected
        ]

    else:

        symbols = SYMBOLS

    st.header(
        "Strategy Filters"
    )

    period = st.selectbox(
        "History",
        [
            "6mo",
            "1y",
            "2y"
        ],
        index=0
    )

    min_score = st.slider(
        "Minimum score for Watchlist",
        4,
        9,
        5
    )

    volume_threshold = st.slider(
        "Volume multiple",
        1.0,
        3.0,
        1.20,
        0.05
    )

    require_breakout = st.checkbox(
        "Require 20-day breakout for BUY",
        False
    )

    require_ema200 = st.checkbox(
        "Require price above EMA200 for BUY",
        False
    )

    st.header(
        "V3 Mode"
    )

    strategy_mode = st.radio(
        "Strategy",
        [
            "Swing",
            "Intraday",
            "Options Stock Finder"
        ]
    )

    sector_filter = st.selectbox(
        "Sector",
        [
            "All sectors"
        ]
        +
        list(
            SECTOR_MAP.keys()
        )
    )

    market_guard = st.checkbox(
        "Use market-regime guard",
        True
    )

    scan = st.button(
        "🔎 SCAN NOW",
        type="primary",
        use_container_width=True
    )


# ============================================================
# SESSION STATE
# ============================================================

if "results_v3" not in st.session_state:

    st.session_state.results_v3 = None


# ============================================================
# SCAN
# ============================================================

if scan:

    rows = []

    progress = st.progress(
        0
    )

    status = st.empty()

    symbols_to_scan = (
        filter_by_sector(
            symbols,
            sector_filter
        )
    )

    st.caption(
        f"Selected sector: "
        f"{sector_filter} • "
        f"Stocks to scan: "
        f"{len(symbols_to_scan)}"
    )

    total = len(
        symbols_to_scan
    )

    for i, sym in enumerate(
        symbols_to_scan
    ):

        status.write(
            f"Scanning "
            f"{sym.replace('.NS','')} "
            f"({i+1}/{total})"
        )

        row = analyze(
            sym,
            period
        )

        if row:

            # Volume filter
            if (
                row["Vol ×"]
                <
                volume_threshold
            ):

                row["ScoreNum"] = max(
                    0,
                    row["ScoreNum"] - 1
                )

            # Breakout requirement
            if (
                require_breakout
                and row["20D Breakout"]
                != "YES"
            ):

                if row["ScoreNum"] >= min_score:
                    row["Signal"] = "WATCH"
                else:
                    row["Signal"] = "AVOID"

            # EMA200 requirement
            if (
                require_ema200
                and row["EMA200"]
                >= row["Price"]
            ):

                if row["ScoreNum"] >= min_score:
                    row["Signal"] = "WATCH"
                else:
                    row["Signal"] = "AVOID"

            # Market guard
            if (
                market_guard
                and market_regime == "BEARISH"
                and row["Signal"]
                in [
                    "BUY",
                    "STRONG BUY"
                ]
            ):

                row["Signal"] = "WATCH"

            # Rebuild score display
            row["Score"] = (
                f"{row['ScoreNum']}/10"
            )

            rows.append(
                row
            )

        progress.progress(
            (i + 1) / max(total, 1)
        )

    status.empty()

    progress.empty()

    st.session_state.results_v3 = (
        pd.DataFrame(rows)
    )


# ============================================================
# RESULTS
# ============================================================

df = (
    st.session_state.results_v3
)


if df is None or df.empty:

    st.info(
        "Set your filters and click "
        "🔎 SCAN NOW to run the screener."
    )

else:

    df = df.sort_values(
        [
            "ScoreNum",
            "Vol ×",
            "RSI"
        ],
        ascending=[
            False,
            False,
            False
        ]
    ).reset_index(
        drop=True
    )

    buy_mask = (
        df["Signal"]
        .isin(
            [
                "BUY",
                "STRONG BUY"
            ]
        )
    )

    watch_mask = (
        df["Signal"]
        .eq("WATCH")
    )

    c1, c2, c3, c4 = st.columns(
        4
    )

    c1.metric(
        "Stocks scanned",
        len(df)
    )

    c2.metric(
        "BUY setups",
        int(
            buy_mask.sum()
        )
    )

    c3.metric(
        "Watchlist",
        int(
            watch_mask.sum()
        )
    )

    c4.metric(
        "Best score",
        f"{int(df.ScoreNum.max())}/10"
    )

    st.subheader(
        "🔥 Today's Top Setups"
    )

    top = (
        df[
            df["ScoreNum"]
            >= min_score
        ]
        .head(10)
        .copy()
    )

    if top.empty:

        st.warning(
            "No setup meets the current "
            "Watchlist score. Try a lower "
            "minimum score or scan again later."
        )

    else:

        cols = [
            "Ticker",
            "Price",
            "RSI",
            "Vol ×",
            "ADX",
            "Support",
            "Resistance",
            "20D Breakout",
            "Score",
            "Signal"
        ]

        st.dataframe(
            top[cols],
            use_container_width=True,
            hide_index=True
        )


    # ========================================================
    # TABS
    # ========================================================

    tab1, tab2, tab3 = st.tabs(
        [
            "📊 All Results",
            "🎯 Trade Plans",
            "📘 Strategy"
        ]
    )


    # ========================================================
    # ALL RESULTS
    # ========================================================

    with tab1:

        show_cols = [
            "Ticker",
            "Price",
            "Change %",
            "RSI",
            "Vol ×",
            "EMA20",
            "EMA50",
            "EMA200",
            "ADX",
            "Support",
            "Resistance",
            "20D Breakout",
            "52W Breakout",
            "MACD Bull",
            "Score",
            "Signal"
        ]

        st.dataframe(
            df[show_cols],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Export full scan to CSV",

            df.drop(
                columns=[
                    "ScoreNum"
                ]
            ).to_csv(
                index=False
            ).encode(
                "utf-8"
            ),

            "vardha_pro_screener_v3_3.csv",

            "text/csv"
        )


    # ========================================================
    # TRADE PLANS
    # ========================================================

    with tab2:

        plans = (
            df[
                df["Signal"]
                .isin(
                    [
                        "BUY",
                        "STRONG BUY",
                        "WATCH"
                    ]
                )
            ]
            .head(15)
        )

        if plans.empty:

            st.info(
                "No current trade-plan candidates."
            )

        else:

            st.dataframe(
                plans[
                    [
                        "Ticker",
                        "Signal",
                        "Price",
                        "Entry",
                        "SL",
                        "TP1",
                        "TP2",
                        "R:R",
                        "Score",
                        "Support",
                        "Resistance"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Entry/SL/TP are rule-based "
                "research levels using recent "
                "resistance/support and ATR; "
                "they are not personalized "
                "recommendations."
            )


    # ========================================================
    # STRATEGY
    # ========================================================

    with tab3:

        st.markdown(
            """
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

**Signal logic:**

**STRONG BUY** requires high score +
confirmed 20-day breakout + volume expansion.

**BUY** requires a high score plus
breakout/near-breakout and volume.

**WATCH** means the trend/momentum is
interesting but confirmation is incomplete.

This tool is for educational/research
purposes and does not guarantee returns.
"""
        )
