# ============================================================
# VARDHA PRO STOCK SCREENER V4
# Advanced Multi-Confirmation Stock Screener
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Vardha Pro Stock Screener V4",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTS
# ============================================================

NIFTY_500_URL = (
    "https://www.niftyindices.com/IndexConstituent/"
    "ind_nifty500list.csv"
)

# Broad fallback universe.
# The application first tries to download the current
# NIFTY-500 constituent list. If unavailable, this universe
# keeps the screener usable.

FALLBACK_SYMBOLS = """
3MINDIA AARTIIND AAVAS ABB ABCAPITAL ABFRL ACC ADANIENSOL
ADANIENT ADANIGREEN ADANIPORTS ADANIPOWER AFFLE AIAENG AJANTAPHARM
ALKEM ALKYLAMINE AMBER AMBUJACEM APARINDS APOLLOHOSP APOLLOTYRE
ASHOKLEY ASIANPAINT ASTRAL ATUL AUBANK AUROPHARMA AXISBANK
BAJAJ-AUTO BAJAJFINSV BAJFINANCE BALKRISIND BANDHANBNK BANKBARODA
BANKINDIA BEL BEML BERGEPAINT BHARATFORG BHARTIARTL BHEL BIOCON
BIRLACORPN BLUESTARCO BOSCHLTD BPCL BRITANNIA BSOFT CANBK
CANFINHOME CDSL CESC CGPOWER CHAMBLFERT CHEMPLAST CHOLAFIN CIPLA
COALINDIA COFORGE COLPAL CONCOR COROMANDEL CROMPTON CUMMINSIND CYIENT
DABUR DALBHARAT DEEPAKNTR DELHIVERY DELTACORP DEVYANI DIVISLAB
DIXON DLF DMART DRREDDY EICHERMOT EIDPARRY EIHOTEL ELGIEQUIP
EMAMILTD ENDURANCE ENGRO EXIDEIND FEDERALBNK FINCABLE FINEORG
FLUOROCHEM FORTIS GAIL GLAND GLENMARK GODREJCP GODREJPROP
GRASIM GRAPHITE GRINDWELL HAL HAVELLS HCLTECH HDFCAMC HDFCBANK
HDFCLIFE HEROMOTOCO HINDALCO HINDCOPPER HINDPETRO HINDUNILVR
HINDZINC HUDCO ICICIBANK ICICIGI ICICIPRULI IDBI IDFCFIRSTB IEX
IGL INDHOTEL INDIACEM INDIAMART INDIANB INDIGO INDUSINDBK INDUSTOWER
INFY INOXWIND IRCTC IRCON IRFC IREDA ITC JINDALSTEL JSWENERGY
JSWSTEEL JUBLFOOD KALYANKJIL KANSAINER KEI KEC KFINTECH KOTAKBANK
KPIL KRBL LALPATHLAB LAURUSLABS LICHSGFIN LT LTIM LUPIN
M&M M&MFIN MANAPPURAM MARICO MARUTI MAXHEALTH MCX MEDANTA
METROPOLIS MGL MOTHERSON MPHASIS MRPL MUTHOOTFIN NATIONALUM
NAVINFLUOR NBCC NESTLEIND NHPC NMDC NLCINDIA NOCIL NTPC OFSS
OIL OBEROIRLTY ONGC PAGEIND PATANJALI PEL PERSISTENT PETRONET
PFC PHOENIXLTD PIDILITIND PIIND POLYCAB POWERGRID PNB PNBHOUSING
PRESTIGE PVRINOX RBLBANK REC RELIANCE RVNL SAIL SAMHI SAPPHIRE
SBICARD SBILIFE SBIN SCHAEFFLER SHREECEM SHRIRAMFIN SIEMENS SJVN
SKFIND SOBHA SOLARINDS SONACOMS SRF STARHEALTH SUNPHARMA SUNTECK
SUPREMEIND SUZLON SYNGENE TATACHEM TATACOMM TATACONSUM TATAELXSI
TATAMOTORS TATAPOWER TATASTEEL TATATECH TCS TECHM TIINDIA TITAN
TORNTPOWER TRENT TVSMOTOR UBL UCOBANK UJJIVANSFB ULTRACEMCO
UNIONBANK UPL VBL VEDL VGUARD VOLTAS WELCORP WELSPUN WESTLIFE
WIPRO YESBANK ZEEL ZOMATO ZYDUSLIFE
"""


# ============================================================
# SECTORS
# ============================================================

SECTOR_MAP = {
    "Banking": {
        "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
        "INDUSINDBK","FEDERALBNK","CANBK","BANKBARODA",
        "IDFCFIRSTB","AUBANK","BANDHANBNK","BANKINDIA","IDBI"
    },

    "IT": {
        "TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM",
        "MPHASIS","PERSISTENT","OFSS","COFORGE"
    },

    "Auto": {
        "MARUTI","M&M","TATAMOTORS","EICHERMOT",
        "HEROMOTOCO","TVSMOTOR","BOSCHLTD","BAJAJ-AUTO"
    },

    "Pharma": {
        "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP",
        "LUPIN","BIOCON","GLENMARK","TORNTPHARM","SYNGENE",
        "MAXHEALTH","FORTIS"
    },

    "Energy": {
        "RELIANCE","NTPC","POWERGRID","ONGC","COALINDIA",
        "BPCL","IOC","GAIL","OIL","PFC","REC","NHPC",
        "TATAPOWER","ADANIGREEN","ADANIPOWER"
    },

    "Metals": {
        "TATASTEEL","JSWSTEEL","HINDALCO","VEDL",
        "JINDALSTEL","HINDCOPPER","SAIL","NMDC","NATIONALUM"
    },

    "FMCG": {
        "ITC","HINDUNILVR","NESTLEIND","BRITANNIA",
        "DABUR","MARICO","GODREJCP","COLPAL","TATACONSUM","VBL"
    },

    "Industrials": {
        "LT","BEL","HAL","SIEMENS","ABB","BHEL",
        "CGPOWER","CUMMINSIND","KEI","POLYCAB","DIXON"
    },

    "Realty": {
        "DLF","GODREJPROP","OBEROIRLTY","PHOENIXLTD","PRESTIGE"
    },

    "Consumer": {
        "TITAN","TRENT","ASIANPAINT","DMART","HAVELLS",
        "CROMPTON","VOLTAS","KALYANKJIL","PAGEIND"
    }
}


# ============================================================
# ============================================================
# UNIVERSE
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def load_universe():

    # --------------------------------------------------------
    # IMPORTANT:
    # Do NOT use pd.read_html() on the NSE CSV URL.
    # It can hang during Streamlit deployment.
    # --------------------------------------------------------

    urls = [
        "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    ]

    # Try official NIFTY 500 CSV with a strict timeout
    for url in urls:

        try:

            import requests
            from io import StringIO

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0 Safari/537.36"
                ),
                "Accept": "text/csv,text/plain,*/*"
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=8
            )

            response.raise_for_status()

            text = response.text.strip()

            if text:

                table = pd.read_csv(
                    StringIO(text)
                )

                symbol_column = None

                for col in table.columns:

                    if "symbol" in str(col).lower():

                        symbol_column = col
                        break

                if symbol_column is not None:

                    symbols = (
                        table[symbol_column]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                        .tolist()
                    )

                    symbols = list(
                        dict.fromkeys(
                            [
                                s
                                for s in symbols
                                if s
                                and s not in [
                                    "NAN",
                                    "SYMBOL"
                                ]
                            ]
                        )
                    )

                    # Accept current NIFTY 500 size
                    # (NIFTY 500 can have slightly more/less
                    # than exactly 500 constituents during changes)
                    if len(symbols) >= 450:

                        return [
                            s
                            if s.endswith(".NS")
                            else s + ".NS"
                            for s in symbols
                        ]

        except Exception:
            continue

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    fallback = [
        s.strip().upper()
        for s in FALLBACK_SYMBOLS.split()
        if s.strip()
    ]

    fallback = list(
        dict.fromkeys(fallback)
    )

    return [
        s
        if s.endswith(".NS")
        else s + ".NS"
        for s in fallback
    ]


# Load universe safely
SYMBOLS = load_universe()

    try:
        tables = pd.read_html(
            "https://www.niftyindices.com/IndexConstituent/"
            "ind_nifty500list.csv"
        )

        for table in tables:

            for col in table.columns:

                if "symbol" in str(col).lower():

                    symbols = (
                        table[col]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                        .tolist()
                    )

                    symbols = list(
                        dict.fromkeys(
                            [
                                s for s in symbols
                                if s not in ["NAN", "SYMBOL"]
                            ]
                        )
                    )

                    if len(symbols) >= 450:

                        return [
                            s + ".NS"
                            for s in symbols
                        ]

    except Exception:
        pass

    return list(
        dict.fromkeys(
            [
                s + ".NS"
                for s in FALLBACK_SYMBOLS.split()
            ]
        )
    )


SYMBOLS = load_universe()


# ============================================================
# INDICATORS
# ============================================================

def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = (
        avg_gain /
        avg_loss.replace(
            0,
            np.nan
        )
    )

    return 100 - (
        100 / (1 + rs)
    )


def atr(df, period=14):

    previous = df["Close"].shift(1)

    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - previous).abs(),
            (df["Low"] - previous).abs()
        ],
        axis=1
    ).max(axis=1)

    return tr.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()


def adx(df, period=14):

    high = df["High"]
    low = df["Low"]

    up = high.diff()
    down = -low.diff()

    plus_dm = pd.Series(
        np.where(
            (up > down) & (up > 0),
            up,
            0
        ),
        index=df.index
    )

    minus_dm = pd.Series(
        np.where(
            (down > up) & (down > 0),
            down,
            0
        ),
        index=df.index
    )

    atr_v = atr(
        df,
        period
    )

    plus_di = (
        100 *
        plus_dm.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()
        /
        atr_v.replace(
            0,
            np.nan
        )
    )

    minus_di = (
        100 *
        minus_dm.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()
        /
        atr_v.replace(
            0,
            np.nan
        )
    )

    dx = (
        100 *
        (plus_di - minus_di).abs()
        /
        (
            plus_di + minus_di
        ).replace(
            0,
            np.nan
        )
    )

    return dx.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()


# ============================================================
# CANDLESTICK
# ============================================================

def candle_pattern(df):

    if len(df) < 3:
        return "Neutral"

    o = float(df["Open"].iloc[-1])
    h = float(df["High"].iloc[-1])
    l = float(df["Low"].iloc[-1])
    c = float(df["Close"].iloc[-1])

    po = float(df["Open"].iloc[-2])
    pc = float(df["Close"].iloc[-2])

    body = abs(c - o)
    candle_range = max(h - l, 0.00001)

    upper = h - max(c, o)
    lower = min(c, o) - l

    if (
        c > o
        and pc < po
        and c >= po
        and o <= pc
    ):
        return "Bullish Engulfing"

    if (
        c < o
        and pc > po
        and o >= pc
        and c <= po
    ):
        return "Bearish Engulfing"

    if (
        lower >= 2 * max(body, 0.01)
        and upper <= max(body, 0.01)
    ):
        return "Hammer"

    if (
        upper >= 2 * max(body, 0.01)
        and lower <= max(body, 0.01)
    ):
        return "Shooting Star"

    if body / candle_range < 0.12:
        return "Doji"

    if c > o:
        return "Bullish Candle"

    if c < o:
        return "Bearish Candle"

    return "Neutral"


# ============================================================
# MARKET REGIME
# ============================================================

@st.cache_data(ttl=900)
def market_regime():

    try:

        df = yf.download(
            "^NSEI",
            period="1y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if df.empty:
            return "UNKNOWN"

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):
            df.columns = (
                df.columns
                .get_level_values(0)
            )

        close = df["Close"].dropna()

        e20 = close.ewm(
            span=20,
            adjust=False
        ).mean()

        e50 = close.ewm(
            span=50,
            adjust=False
        ).mean()

        e200 = close.ewm(
            span=200,
            adjust=False
        ).mean()

        current = float(
            close.iloc[-1]
        )

        rv = float(
            rsi(close).iloc[-1]
        )

        if (
            current > e20.iloc[-1]
            and e20.iloc[-1] > e50.iloc[-1]
            and current > e200.iloc[-1]
            and rv >= 52
        ):
            return "BULLISH"

        if (
            current < e20.iloc[-1]
            and e20.iloc[-1] < e50.iloc[-1]
            and current < e200.iloc[-1]
            and rv <= 48
        ):
            return "BEARISH"

        return "SIDEWAYS"

    except Exception:
        return "UNKNOWN"


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_dataframe(df):

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
        x in df.columns
        for x in required
    ):
        return None

    df = df.dropna(
        subset=required
    ).copy()

    if len(df) < 60:
        return None

    return df


# ============================================================
# ANALYZE STOCK
# ============================================================

def analyze_stock(
    symbol,
    df,
    strategy,
    min_score,
    volume_threshold,
    market
):

    try:

        df = prepare_dataframe(
            df
        )

        if df is None:
            return None

        close = df["Close"]
        volume = df["Volume"].replace(
            0,
            np.nan
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

        adx_v = adx(
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

        vol20 = volume.rolling(
            20
        ).mean()

        current_price = float(
            close.iloc[-1]
        )

        previous_price = float(
            close.iloc[-2]
        )

        current_rsi = float(
            r.iloc[-1]
        )

        current_atr = float(
            a.iloc[-1]
        )

        current_adx = float(
            adx_v.iloc[-1]
        )

        current_vol = float(
            volume.iloc[-1]
        )

        average_vol = float(
            vol20.iloc[-1]
        )

        if average_vol <= 0:
            volume_multiple = 0
        else:
            volume_multiple = (
                current_vol /
                average_vol
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

        low52 = float(
            df["Low"]
            .tail(252)
            .min()
        )

        breakout20 = (
            current_price >
            resistance20
        )

        near_breakout = (
            current_price >=
            resistance20 * 0.985
        )

        breakout52 = (
            current_price >=
            high52 * 0.995
        )

        above20 = (
            current_price >
            float(ema20.iloc[-1])
        )

        above50 = (
            current_price >
            float(ema50.iloc[-1])
        )

        above200 = (
            current_price >
            float(ema200.iloc[-1])
        )

        ema_stack = (
            above20
            and above50
            and above200
            and ema20.iloc[-1]
            > ema50.iloc[-1]
            > ema200.iloc[-1]
        )

        rsi_momentum = (
            52 <= current_rsi <= 75
        )

        macd_bull = (
            float(macd.iloc[-1])
            >
            float(macd_signal.iloc[-1])
        )

        volume_good = (
            volume_multiple
            >= volume_threshold
        )

        adx_good = (
            current_adx >= 20
        )

        candle = candle_pattern(
            df
        )

        bullish_candle = candle in [
            "Bullish Engulfing",
            "Hammer",
            "Bullish Candle"
        ]

        bearish_candle = candle in [
            "Bearish Engulfing",
            "Shooting Star",
            "Bearish Candle"
        ]

        # ----------------------------------------------------
        # Multi-confirmation scoring
        # ----------------------------------------------------

        trend_score = sum([
            above20,
            above50,
            above200,
            ema_stack
        ])

        momentum_score = sum([
            rsi_momentum,
            macd_bull,
            adx_good
        ])

        breakout_score = sum([
            breakout20,
            near_breakout,
            breakout52
        ])

        volume_score = int(
            volume_good
        )

        candle_score = int(
            bullish_candle
        )

        raw_score = (
            trend_score
            +
            momentum_score
            +
            breakout_score
            +
            volume_score
            +
            candle_score
        )

        # Maximum = 12
        max_score = 12

        # Convert to /10
        score10 = round(
            (
                raw_score /
                max_score
            ) * 10,
            1
        )

        # ----------------------------------------------------
        # Strategy-specific confirmation
        # ----------------------------------------------------

        if strategy == "Swing":

            strategy_ok = (
                above50
                and
                above200
                and
                adx_good
            )

        elif strategy == "Intraday":

            strategy_ok = (
                above20
                and
                (
                    volume_good
                    or
                    breakout20
                )
            )

        else:

            strategy_ok = (
                volume_good
                and
                (
                    breakout20
                    or
                    near_breakout
                )
            )

        # ----------------------------------------------------
        # Market guard
        # ----------------------------------------------------

        market_ok = True

        if market == "BEARISH":

            market_ok = (
                above200
                and
                score10 >= 7
            )

        # ----------------------------------------------------
        # Signal
        # ----------------------------------------------------

        strong_confirmation = (
            score10 >= 8
            and strategy_ok
            and market_ok
            and (
                breakout20
                or
                near_breakout
            )
            and volume_good
        )

        normal_confirmation = (
            score10 >= 7
            and strategy_ok
            and market_ok
        )

        if strong_confirmation:

            signal = "STRONG BUY"

        elif normal_confirmation:

            signal = "BUY"

        elif score10 >= min_score:

            signal = "WATCH"

        else:

            signal = "AVOID"

        if bearish_candle and signal == "STRONG BUY":
            signal = "BUY"

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        confidence = min(
            99,
            max(
                20,
                round(
                    score10 * 10
                    +
                    (5 if volume_good else 0)
                    +
                    (5 if breakout20 else 0)
                    +
                    (5 if bullish_candle else 0)
                    -
                    (5 if market == "BEARISH" else 0)
                )
            )
        )

        # ----------------------------------------------------
        # Trade plan
        # ----------------------------------------------------

        if breakout20 or near_breakout:

            entry = max(
                current_price,
                resistance20 * 1.002
            )

        else:

            entry = current_price

        support = max(
            support20,
            float(ema20.iloc[-1])
            -
            0.5 * current_atr
        )

        sl = min(
            entry -
            1.5 * current_atr,
            support
        )

        if sl >= entry:

            sl = (
                entry -
                1.5 * current_atr
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

        rr = (
            (tp1 - entry) /
            risk
            if risk > 0
            else 0
        )

        # ----------------------------------------------------
        # Sector
        # ----------------------------------------------------

        clean_symbol = (
            symbol
            .replace(
                ".NS",
                ""
            )
            .upper()
        )

        sector = "Other"

        for sec, stocks in SECTOR_MAP.items():

            if clean_symbol in stocks:

                sector = sec
                break

        return {

            "Ticker": clean_symbol,

            "Price": round(
                current_price,
                2
            ),

            "Change %": round(
                (
                    current_price /
                    previous_price -
                    1
                ) * 100,
                2
            ),

            "RSI": round(
                current_rsi,
                1
            ),

            "Vol ×": round(
                volume_multiple,
                2
            ),

            "ADX": round(
                current_adx,
                1
            ),

            "EMA20": round(
                float(
                    ema20.iloc[-1]
                ),
                2
            ),

            "EMA50": round(
                float(
                    ema50.iloc[-1]
                ),
                2
            ),

            "EMA200": round(
                float(
                    ema200.iloc[-1]
                ),
                2
            ),

            "Support": round(
                support,
                2
            ),

            "Resistance": round(
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

            "MACD":
                "BULLISH"
                if macd_bull
                else "BEARISH",

            "Candle": candle,

            "Sector": sector,

            "Entry": round(
                entry,
                2
            ),

            "SL": round(
                sl,
                2
            ),

            "TP1": round(
                tp1,
                2
            ),

            "TP2": round(
                tp2,
                2
            ),

            "R:R":
                f"1:{rr:.1f}",

            "Score":
                f"{score10:.1f}/10",

            "ScoreNum":
                score10,

            "Confidence":
                f"{confidence}%",

            "ConfidenceNum":
                confidence,

            "Signal":
                signal
        }

    except Exception:
        return None


# ============================================================
# FAST BATCH DOWNLOAD
# ============================================================

@st.cache_data(ttl=900, show_spinner=False)
def download_market_data(
    symbols,
    period
):

    try:

        data = yf.download(
            tickers=symbols,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="column"
        )

        return data

    except Exception:
        return None


# ============================================================
# GET ONE STOCK FROM BATCH
# ============================================================

def extract_stock(
    batch,
    symbol
):

    try:

        if batch is None or batch.empty:
            return None

        if isinstance(
            batch.columns,
            pd.MultiIndex
        ):

            if symbol not in batch.columns.get_level_values(1):

                return None

            stock = batch.xs(
                symbol,
                axis=1,
                level=1
            )

            return stock

        return batch

    except Exception:
        return None


# ============================================================
# CHART
# ============================================================

def show_chart(
    symbol,
    period
):

    try:

        data = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        data = prepare_dataframe(
            data
        )

        if data is None:
            return

        chart_df = data[
            [
                "Close"
            ]
        ].copy()

        chart_df["EMA20"] = (
            chart_df["Close"]
            .ewm(
                span=20,
                adjust=False
            )
            .mean()
        )

        chart_df["EMA50"] = (
            chart_df["Close"]
            .ewm(
                span=50,
                adjust=False
            )
            .mean()
        )

        chart_df["EMA200"] = (
            chart_df["Close"]
            .ewm(
                span=200,
                adjust=False
            )
            .mean()
        )

        st.line_chart(
            chart_df[
                [
                    "Close",
                    "EMA20",
                    "EMA50",
                    "EMA200"
                ]
            ]
        )

    except Exception:

        st.warning(
            "Chart data unavailable."
        )


# ============================================================
# HEADER
# ============================================================

regime = market_regime()

st.title(
    "📈 Vardha Pro Stock Screener V4"
)

st.caption(
    f"Universe: {len(SYMBOLS)} symbols • "
    f"Market Regime: {regime}"
)

st.caption(
    "Advanced trend + momentum + breakout + "
    "volume + price-action research framework"
)

st.warning(
    "Educational/research tool only. "
    "Signals are rule-based and are not guaranteed "
    "profits or personalized investment advice."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Screener Settings"
    )

    universe_mode = st.radio(
        "Universe",
        [
            "NIFTY 500",
            "Custom symbols"
        ]
    )

    if universe_mode == "Custom symbols":

        custom = st.text_area(
            "Enter symbols",
            "RELIANCE, TCS, INFY, HDFCBANK"
        )

        selected_symbols = [
            x.strip().upper()
            for x in custom
            .replace(
                "\n",
                ","
            )
            .split(",")
            if x.strip()
        ]

        scan_symbols = [
            x
            if x.endswith(".NS")
            else x + ".NS"
            for x in selected_symbols
        ]

    else:

        scan_symbols = SYMBOLS

    st.header(
        "🎯 Strategy"
    )

    strategy = st.radio(
        "Strategy Mode",
        [
            "Swing",
            "Intraday",
            "Options Stock Finder"
        ]
    )

    history = st.selectbox(
        "Historical data",
        [
            "6mo",
            "1y",
            "2y"
        ]
    )

    min_score = st.slider(
        "Minimum score",
        5.0,
        9.0,
        7.0,
        0.5
    )

    volume_threshold = st.slider(
        "Minimum volume ×",
        1.0,
        3.0,
        1.20,
        0.05
    )

    st.header(
        "🏦 Sector"
    )

    sector = st.selectbox(
        "Sector filter",
        [
            "All sectors"
        ]
        +
        list(
            SECTOR_MAP.keys()
        )
    )

    st.header(
        "🛡️ Risk Filters"
    )

    market_guard = st.checkbox(
        "Market regime guard",
        True
    )

    require_breakout = st.checkbox(
        "Require breakout",
        False
    )

    strong_only = st.checkbox(
        "Show only BUY setups",
        False
    )

    st.header(
        "🔎 Individual Stock"
    )

    search_stock = st.text_input(
        "Search stock",
        placeholder="RELIANCE"
    )

    scan_button = st.button(
        "🚀 SCAN 500 STOCKS",
        type="primary",
        use_container_width=True
    )


# ============================================================
# SECTOR FILTER
# ============================================================

if sector != "All sectors":

    allowed = SECTOR_MAP.get(
        sector,
        set()
    )

    scan_symbols = [
        s
        for s in scan_symbols
        if s.replace(
            ".NS",
            ""
        ).upper()
        in allowed
    ]


# ============================================================
# SCAN
# ============================================================

if scan_button:

    start_time = datetime.now()

    progress = st.progress(
        0
    )

    status = st.empty()

    results = []

    batch = download_market_data(
        scan_symbols,
        history
    )

    total = len(
        scan_symbols
    )

    for i, symbol in enumerate(
        scan_symbols
    ):

        status.write(
            f"Scanning {symbol.replace('.NS','')} "
            f"({i+1}/{total})"
        )

        stock_df = extract_stock(
            batch,
            symbol
        )

        row = analyze_stock(
            symbol,
            stock_df,
            strategy,
            min_score,
            volume_threshold,
            regime
        )

        if row is not None:

            if (
                require_breakout
                and row["20D Breakout"] != "YES"
            ):
                row["Signal"] = "WATCH"

            if (
                market_guard
                and regime == "BEARISH"
                and row["Signal"]
                in [
                    "BUY",
                    "STRONG BUY"
                ]
            ):
                row["Signal"] = "WATCH"

            if (
                strong_only
                and row["Signal"]
                not in [
                    "BUY",
                    "STRONG BUY"
                ]
            ):
                pass
            else:
                results.append(
                    row
                )

        progress.progress(
            (i + 1) /
            max(total, 1)
        )

    status.empty()
    progress.empty()

    result_df = pd.DataFrame(
        results
    )

    if not result_df.empty:

        result_df = result_df.sort_values(
            [
                "ScoreNum",
                "ConfidenceNum",
                "Vol ×"
            ],
            ascending=[
                False,
                False,
                False
            ]
        ).reset_index(
            drop=True
        )

    st.session_state["v4_results"] = (
        result_df
    )

    elapsed = (
        datetime.now() -
        start_time
    ).total_seconds()

    st.session_state["v4_scan_time"] = (
        round(elapsed, 1)
    )


# ============================================================
# RESULTS
# ============================================================

if "v4_results" not in st.session_state:

    st.info(
        "Configure your filters and press "
        "🚀 SCAN 500 STOCKS."
    )

else:

    df = st.session_state[
        "v4_results"
    ]

    if df is None or df.empty:

        st.warning(
            "No valid setups found with the "
            "current filters."
        )

    else:

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        strong_count = int(
            (
                df["Signal"]
                == "STRONG BUY"
            ).sum()
        )

        buy_count = int(
            (
                df["Signal"]
                == "BUY"
            ).sum()
        )

        watch_count = int(
            (
                df["Signal"]
                == "WATCH"
            ).sum()
        )

        best_score = float(
            df["ScoreNum"].max()
        )

        scan_time = st.session_state.get(
            "v4_scan_time",
            0
        )

        c1, c2, c3, c4, c5 = st.columns(
            5
        )

        c1.metric(
            "Stocks scanned",
            len(df)
        )

        c2.metric(
            "🔥 Strong BUY",
            strong_count
        )

        c3.metric(
            "🟢 BUY",
            buy_count
        )

        c4.metric(
            "👀 Watch",
            watch_count
        )

        c5.metric(
            "⚡ Scan time",
            f"{scan_time}s"
        )

        # ----------------------------------------------------
        # TOP 10
        # ----------------------------------------------------

        st.subheader(
            "🔥 TOP 10 STRONG SETUPS"
        )

        top10 = df[
            df["Signal"]
            .isin(
                [
                    "STRONG BUY",
                    "BUY"
                ]
            )
        ].head(10)

        if top10.empty:

            st.info(
                "No BUY setup currently meets "
                "the selected confirmation rules."
            )

        else:

            top_cols = [
                "Ticker",
                "Price",
                "Signal",
                "Score",
                "Confidence",
                "RSI",
                "Vol ×",
                "ADX",
                "Candle",
                "20D Breakout",
                "Entry",
                "SL",
                "TP1",
                "TP2",
                "R:R"
            ]

            st.dataframe(
                top10[top_cols],
                use_container_width=True,
                hide_index=True
            )

        # ----------------------------------------------------
        # TABS
        # ----------------------------------------------------

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "📊 All Results",
                "🎯 Trade Plans",
                "📋 Watchlist",
                "📉 Stock Chart",
                "📘 Strategy"
            ]
        )

        # ----------------------------------------------------
        # ALL RESULTS
        # ----------------------------------------------------

        with tab1:

            all_cols = [
                "Ticker",
                "Price",
                "Change %",
                "Signal",
                "Score",
                "Confidence",
                "RSI",
                "Vol ×",
                "ADX",
                "EMA20",
                "EMA50",
                "EMA200",
                "Candle",
                "Sector",
                "Support",
                "Resistance",
                "20D Breakout",
                "52W Breakout",
                "MACD"
            ]

            st.dataframe(
                df[all_cols],
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Download Full CSV",

                df.drop(
                    columns=[
                        "ScoreNum",
                        "ConfidenceNum"
                    ],
                    errors="ignore"
                )
                .to_csv(
                    index=False
                )
                .encode(
                    "utf-8"
                ),

                "vardha_pro_screener_v4.csv",

                "text/csv"
            )

        # ----------------------------------------------------
        # TRADE PLANS
        # ----------------------------------------------------

        with tab2:

            plans = df[
                df["Signal"]
                .isin(
                    [
                        "STRONG BUY",
                        "BUY"
                    ]
                )
            ].head(20)

            if plans.empty:

                st.info(
                    "No current trade-plan candidates."
                )

            else:

                plan_cols = [
                    "Ticker",
                    "Signal",
                    "Confidence",
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

                st.dataframe(
                    plans[plan_cols],
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    "Entry, SL and targets are "
                    "rule-based research levels."
                )

        # ----------------------------------------------------
        # WATCHLIST
        # ----------------------------------------------------

        with tab3:

            watch = df[
                df["Signal"]
                == "WATCH"
            ].head(30)

            if watch.empty:

                st.info(
                    "No watchlist candidates."
                )

            else:

                watch_cols = [
                    "Ticker",
                    "Price",
                    "Score",
                    "Confidence",
                    "RSI",
                    "Vol ×",
                    "ADX",
                    "Candle",
                    "Sector",
                    "20D Breakout"
                ]

                st.dataframe(
                    watch[watch_cols],
                    use_container_width=True,
                    hide_index=True
                )

        # ----------------------------------------------------
        # CHART
        # ----------------------------------------------------

        with tab4:

            available = (
                df["Ticker"]
                .tolist()
            )

            if available:

                chart_stock = st.selectbox(
                    "Select stock",
                    available
                )

                chart_period = st.selectbox(
                    "Chart period",
                    [
                        "3mo",
                        "6mo",
                        "1y",
                        "2y"
                    ],
                    index=1
                )

                st.subheader(
                    f"📈 {chart_stock}"
                )

                show_chart(
                    chart_stock + ".NS",
                    chart_period
                )

        # ----------------------------------------------------
        # STRATEGY
        # ----------------------------------------------------

        with tab5:

            st.markdown(
                """
### 🎯 V4 Multi-Confirmation Engine

The V4 engine combines:

**Trend**
- EMA20
- EMA50
- EMA200
- EMA trend stacking

**Momentum**
- RSI
- MACD
- ADX

**Breakout**
- 20-day resistance
- Near-breakout
- 52-week breakout

**Volume**
- Current volume vs 20-day average

**Price Action**
- Bullish Engulfing
- Bearish Engulfing
- Hammer
- Shooting Star
- Doji

### ⭐ Confidence Score

The confidence number is a
**technical-rule based confidence score**.
It is NOT a guaranteed probability of profit.

### 📈 Swing

Swing mode gives more weight to:
- EMA50
- EMA200
- ADX
- Trend structure
- Breakout confirmation

### 📊 Intraday

Intraday mode gives more weight to:
- EMA20
- Momentum
- Volume
- Breakout

### ⚡ Options Stock Finder

This mode looks for liquid,
high-momentum stocks with:
- Volume expansion
- Breakout/near-breakout
- Strong trend
- Higher technical score

### 🟢 Market Regime

The screener checks NIFTY trend:

🟢 BULLISH  
🟡 SIDEWAYS  
🔴 BEARISH

When market guard is enabled,
strong BUY signals are restricted
during weak market conditions.

### ⚠️ Important

This screener is an educational/research
tool. It does not guarantee returns and
does not constitute personalized investment
advice.
"""
            )


# ============================================================
# INDIVIDUAL STOCK SEARCH
# ============================================================

if search_stock:

    clean = (
        search_stock
        .strip()
        .upper()
    )

    if clean:

        if not clean.endswith(
            ".NS"
        ):
            clean += ".NS"

        st.divider()

        st.subheader(
            f"🔎 Individual Analysis: "
            f"{clean.replace('.NS','')}"
        )

        try:

            individual = yf.download(
                clean,
                period="1y",
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False
            )

            individual = prepare_dataframe(
                individual
            )

            if individual is None:

                st.error(
                    "Stock data not available."
                )

            else:

                analysis = analyze_stock(
                    clean,
                    individual,
                    strategy,
                    min_score,
                    volume_threshold,
                    regime
                )

                if analysis:

                    a1, a2, a3, a4 = st.columns(
                        4
                    )

                    a1.metric(
                        "Signal",
                        analysis["Signal"]
                    )

                    a2.metric(
                        "Score",
                        analysis["Score"]
                    )

                    a3.metric(
                        "Confidence",
                        analysis["Confidence"]
                    )

                    a4.metric(
                        "RSI",
                        analysis["RSI"]
                    )

                    details = pd.DataFrame(
                        [
                            {
                                "Ticker": analysis["Ticker"],
                                "Price": analysis["Price"],
                                "Entry": analysis["Entry"],
                                "SL": analysis["SL"],
                                "TP1": analysis["TP1"],
                                "TP2": analysis["TP2"],
                                "R:R": analysis["R:R"],
                                "Candle": analysis["Candle"],
                                "Sector": analysis["Sector"],
                                "20D Breakout": analysis["20D Breakout"],
                                "52W Breakout": analysis["52W Breakout"]
                            }
                        ]
                    )

                    st.dataframe(
                        details,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.subheader(
                        "📉 Technical Chart"
                    )

                    show_chart(
                        clean,
                        "1y"
                    )

        except Exception:

            st.error(
                "Unable to analyze this stock."
            )
