# ============================================================
# VARDHA PRO STOCK SCREENER V5.1
# OPTIMIZED BEST-OF-THE-BEST MULTI-TIMEFRAME ENGINE
#
# PIPELINE
# ------------------------------------------------------------
# NIFTY 500
#    ↓
# DAILY  → Trend + Momentum + Breakout + Volume + Structure
#    ↓
# DAILY PRE-FILTER
#    ↓
# 1H     → Trend + Momentum + Confirmation
#    ↓
# 15M    → Entry Timing + Micro Breakout + Price Action
#    ↓
# SECTOR + MARKET REGIME
#    ↓
# FINAL QUALITY SCORE 0-100
#    ↓
# TOP 5-15 BEST SETUPS
#
# Timeframes:
# 1D  = Stock Selection
# 1H  = Setup Confirmation
# 15M = Entry Timing
#
# IMPORTANT:
# This is a rule-based technical research/screening tool.
# It does NOT guarantee profit or future performance.
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests

from io import StringIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Vardha Pro Stock Screener V5.1",
    page_icon="🔥",
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

MIN_DAILY_BARS = 220
MIN_HOURLY_BARS = 60
MIN_15M_BARS = 50

TOP_MIN = 5
TOP_MAX = 15

MAX_DAILY_PREFILTER = 150
MAX_INTRADAY_CANDIDATES = 90

MAX_WORKERS_DAILY = 8
MAX_WORKERS_INTRADAY = 10

CACHE_TTL_DAILY = 1800
CACHE_TTL_INTRADAY = 900
CACHE_TTL_REGIME = 900
CACHE_TTL_UNIVERSE = 86400


# ============================================================
# FALLBACK UNIVERSE
# ============================================================

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
EMAMILTD ENDURANCE EXIDEIND FEDERALBNK FINCABLE FINEORG
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
# SECTOR MAP
# ============================================================

SECTOR_MAP = {

    "Banking": {
        "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK",
        "KOTAKBANK", "INDUSINDBK", "FEDERALBNK",
        "CANBK", "BANKBARODA", "IDFCFIRSTB",
        "AUBANK", "BANDHANBNK", "BANKINDIA", "IDBI"
    },

    "IT": {
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM",
        "LTIM", "MPHASIS", "PERSISTENT", "OFSS", "COFORGE"
    },

    "Auto": {
        "MARUTI", "M&M", "TATAMOTORS", "EICHERMOT",
        "HEROMOTOCO", "TVSMOTOR", "BOSCHLTD",
        "BAJAJ-AUTO"
    },

    "Pharma": {
        "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB",
        "APOLLOHOSP", "LUPIN", "BIOCON", "GLENMARK",
        "SYNGENE", "MAXHEALTH", "FORTIS"
    },

    "Energy": {
        "RELIANCE", "NTPC", "POWERGRID", "ONGC",
        "COALINDIA", "BPCL", "GAIL", "OIL", "PFC",
        "REC", "NHPC", "TATAPOWER", "ADANIGREEN",
        "ADANIPOWER"
    },

    "Metals": {
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL",
        "JINDALSTEL", "HINDCOPPER", "SAIL", "NMDC",
        "NATIONALUM"
    },

    "FMCG": {
        "ITC", "HINDUNILVR", "NESTLEIND", "BRITANNIA",
        "DABUR", "MARICO", "GODREJCP", "COLPAL",
        "TATACONSUM", "VBL"
    },

    "Industrials": {
        "LT", "BEL", "HAL", "SIEMENS", "ABB", "BHEL",
        "CGPOWER", "CUMMINSIND", "KEI", "POLYCAB",
        "DIXON"
    },

    "Realty": {
        "DLF", "GODREJPROP", "OBEROIRLTY",
        "PHOENIXLTD", "PRESTIGE"
    },

    "Consumer": {
        "TITAN", "TRENT", "ASIANPAINT", "DMART",
        "HAVELLS", "CROMPTON", "VOLTAS",
        "KALYANKJIL", "PAGEIND"
    }
}


# ============================================================
# UTILITY
# ============================================================

def safe_float(value, default=0.0):

    try:

        if pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


# ============================================================
# LOAD NIFTY 500
# ============================================================

@st.cache_data(
    ttl=CACHE_TTL_UNIVERSE,
    show_spinner=False
)
def load_universe():

    try:

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
            NIFTY_500_URL,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        table = pd.read_csv(
            StringIO(response.text)
        )

        symbol_col = None

        for col in table.columns:

            if "symbol" in str(col).lower():

                symbol_col = col
                break

        if symbol_col is not None:

            symbols = (
                table[symbol_col]
                .astype(str)
                .str.strip()
                .str.upper()
                .tolist()
            )

            symbols = list(
                dict.fromkeys(
                    [
                        x
                        for x in symbols
                        if x
                        and x not in ["NAN", "SYMBOL"]
                    ]
                )
            )

            if len(symbols) >= 450:

                return [
                    x if x.endswith(".NS")
                    else x + ".NS"
                    for x in symbols
                ]

    except Exception:
        pass

    fallback = [
        x.strip().upper()
        for x in FALLBACK_SYMBOLS.split()
        if x.strip()
    ]

    fallback = list(
        dict.fromkeys(fallback)
    )

    return [
        x if x.endswith(".NS")
        else x + ".NS"
        for x in fallback
    ]


SYMBOLS = load_universe()


# ============================================================
# DATA CLEANING
# ============================================================

def clean_yf_dataframe(df):

    if df is None or df.empty:
        return None

    df = df.copy()

    try:

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):

            # Handle common yfinance multi-index formats
            level0 = list(df.columns.get_level_values(0))

            if all(
                x in level0
                for x in [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"
                ]
            ):

                df.columns = (
                    df.columns
                    .get_level_values(0)
                )

            else:

                # Try second level
                df.columns = (
                    df.columns
                    .get_level_values(-1)
                )

    except Exception:

        return None

    required = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    if not all(
        col in df.columns
        for col in required
    ):

        return None

    df = df[
        required
    ].copy()

    for col in required:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    df = df.dropna(
        subset=required
    )

    if df.empty:
        return None

    return df


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

    result = (
        100 -
        (
            100 /
            (1 + rs)
        )
    )

    return result


def atr(df, period=14):

    previous = df["Close"].shift(1)

    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (
                df["High"] -
                previous
            ).abs(),
            (
                df["Low"] -
                previous
            ).abs()
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
            (
                (up > down) &
                (up > 0)
            ),
            up,
            0
        ),
        index=df.index
    )

    minus_dm = pd.Series(
        np.where(
            (
                (down > up) &
                (down > 0)
            ),
            down,
            0
        ),
        index=df.index
    )

    atr_value = atr(
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
        atr_value.replace(
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
        atr_value.replace(
            0,
            np.nan
        )
    )

    denominator = (
        plus_di +
        minus_di
    ).replace(
        0,
        np.nan
    )

    dx = (
        100 *
        (
            plus_di -
            minus_di
        ).abs()
        /
        denominator
    )

    return dx.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()


# ============================================================
# CANDLE / PRICE ACTION
# ============================================================

def candle_pattern(df):

    if df is None or len(df) < 3:
        return "Neutral"

    o = safe_float(
        df["Open"].iloc[-1]
    )

    h = safe_float(
        df["High"].iloc[-1]
    )

    l = safe_float(
        df["Low"].iloc[-1]
    )

    c = safe_float(
        df["Close"].iloc[-1]
    )

    po = safe_float(
        df["Open"].iloc[-2]
    )

    pc = safe_float(
        df["Close"].iloc[-2]
    )

    body = abs(
        c - o
    )

    candle_range = max(
        h - l,
        0.00001
    )

    upper = (
        h -
        max(c, o)
    )

    lower = (
        min(c, o) -
        l
    )

    if (
        c > o
        and
        pc < po
        and
        c >= po
        and
        o <= pc
    ):
        return "Bullish Engulfing"

    if (
        c < o
        and
        pc > po
        and
        o >= pc
        and
        c <= po
    ):
        return "Bearish Engulfing"

    if (
        lower >= 2 * max(
            body,
            0.01
        )
        and
        upper <= max(
            body,
            0.01
        )
    ):
        return "Hammer"

    if (
        upper >= 2 * max(
            body,
            0.01
        )
        and
        lower <= max(
            body,
            0.01
        )
    ):
        return "Shooting Star"

    if (
        body /
        candle_range
        < 0.12
    ):
        return "Doji"

    if c > o:
        return "Bullish Candle"

    if c < o:
        return "Bearish Candle"

    return "Neutral"


# ============================================================
# MARKET REGIME
# ============================================================

@st.cache_data(
    ttl=CACHE_TTL_REGIME,
    show_spinner=False
)
def market_regime():

    try:

        df = yf.download(
            "^NSEI",
            period="2y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        df = clean_yf_dataframe(
            df
        )

        if df is None or len(df) < 200:
            return "UNKNOWN"

        close = df["Close"]

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

        current = safe_float(
            close.iloc[-1]
        )

        current_rsi = safe_float(
            rsi(close).iloc[-1]
        )

        slope20 = (
            ema20.iloc[-1] >
            ema20.iloc[-6]
        )

        if (
            current > ema20.iloc[-1]
            and
            ema20.iloc[-1] >
            ema50.iloc[-1]
            and
            ema50.iloc[-1] >
            ema200.iloc[-1]
            and
            current_rsi >= 52
            and
            slope20
        ):

            return "BULLISH"

        if (
            current < ema20.iloc[-1]
            and
            ema20.iloc[-1] <
            ema50.iloc[-1]
            and
            ema50.iloc[-1] <
            ema200.iloc[-1]
            and
            current_rsi <= 48
        ):

            return "BEARISH"

        return "SIDEWAYS"

    except Exception:

        return "UNKNOWN"


# ============================================================
# SECTOR
# ============================================================

def get_sector(symbol):

    clean = (
        symbol
        .replace(".NS", "")
        .upper()
    )

    for sector, stocks in SECTOR_MAP.items():

        if clean in stocks:
            return sector

    return "Other"


# ============================================================
# DAILY ANALYSIS
# ============================================================

def analyze_daily(df):

    df = clean_yf_dataframe(
        df
    )

    if (
        df is None
        or
        len(df) < MIN_DAILY_BARS
    ):
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

    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    macd = (
        ema12 -
        ema26
    )

    macd_signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    vol20 = volume.rolling(
        20
    ).mean()

    price = safe_float(
        close.iloc[-1]
    )

    previous = safe_float(
        close.iloc[-2]
    )

    current_rsi = safe_float(
        r.iloc[-1]
    )

    current_atr = safe_float(
        a.iloc[-1]
    )

    current_adx = safe_float(
        adx_value.iloc[-1]
    )

    current_vol = safe_float(
        volume.iloc[-1]
    )

    average_volume = safe_float(
        vol20.iloc[-1]
    )

    if average_volume > 0:

        rel_volume = (
            current_vol /
            average_volume
        )

    else:

        rel_volume = 0

    resistance20 = safe_float(
        df["High"]
        .iloc[-21:-1]
        .max()
    )

    support20 = safe_float(
        df["Low"]
        .iloc[-21:-1]
        .min()
    )

    high52 = safe_float(
        df["High"]
        .tail(252)
        .max()
    )

    low52 = safe_float(
        df["Low"]
        .tail(252)
        .min()
    )

    ema20_value = safe_float(
        ema20.iloc[-1]
    )

    ema50_value = safe_float(
        ema50.iloc[-1]
    )

    ema200_value = safe_float(
        ema200.iloc[-1]
    )

    above20 = (
        price >
        ema20_value
    )

    above50 = (
        price >
        ema50_value
    )

    above200 = (
        price >
        ema200_value
    )

    ema_stack = (
        above20
        and
        above50
        and
        above200
        and
        ema20_value >
        ema50_value >
        ema200_value
    )

    trend_slope = (
        ema20.iloc[-1] >
        ema20.iloc[-6]
        and
        ema50.iloc[-1] >
        ema50.iloc[-6]
    )

    breakout20 = (
        price >
        resistance20
    )

    near_breakout = (
        price >=
        resistance20 * 0.985
    )

    breakout52 = (
        price >=
        high52 * 0.995
    )

    macd_bull = (
        macd.iloc[-1] >
        macd_signal.iloc[-1]
    )

    macd_rising = (
        macd.iloc[-1] >
        macd.iloc[-2]
    )

    rsi_good = (
        52 <= current_rsi <= 70
    )

    adx_good = (
        current_adx >= 20
    )

    volume_good = (
        rel_volume >= 1.20
    )

    volume_strong = (
        rel_volume >= 1.50
    )

    candle = candle_pattern(
        df
    )

    bullish_candle = candle in [
        "Bullish Engulfing",
        "Hammer",
        "Bullish Candle"
    ]

    strong_bullish_candle = candle in [
        "Bullish Engulfing",
        "Hammer"
    ]

    bearish_candle = candle in [
        "Bearish Engulfing",
        "Shooting Star",
        "Bearish Candle"
    ]

    distance_from_ema20 = (
        (
            price -
            ema20_value
        )
        /
        max(
            ema20_value,
            0.00001
        )
    ) * 100

    # More practical anti-chasing filter
    overextended = (
        distance_from_ema20 > 8
        or
        (
            current_atr > 0
            and
            (
                price -
                ema20_value
            ) >
            2.5 * current_atr
        )
    )

    # ========================================================
    # DAILY SCORE / 40
    # ========================================================

    daily_score = 0

    # Trend = 12
    daily_score += 3 if above20 else 0
    daily_score += 3 if above50 else 0
    daily_score += 3 if above200 else 0
    daily_score += 3 if ema_stack else 0

    # Momentum = 8
    daily_score += 3 if rsi_good else 0
    daily_score += 2 if macd_bull else 0
    daily_score += 3 if adx_good else 0

    # Breakout = 8
    if breakout20:
        daily_score += 4

    elif near_breakout:
        daily_score += 2

    if breakout52:
        daily_score += 2

    if (
        breakout20
        and
        macd_rising
    ):
        daily_score += 2

    # Volume = 5
    daily_score += 3 if volume_good else 0
    daily_score += 2 if volume_strong else 0

    # Price action = 4
    daily_score += 4 if strong_bullish_candle else 0
    daily_score += 2 if (
        bullish_candle
        and
        not strong_bullish_candle
    ) else 0

    # Structure = 3
    daily_score += 3 if trend_slope else 0

    if overextended:
        daily_score -= 6

    daily_score = max(
        0,
        min(
            40,
            daily_score
        )
    )

    return {

        "price": price,
        "previous": previous,

        "change_pct": (
            (
                price /
                max(
                    previous,
                    0.00001
                )
                - 1
            ) * 100
        ),

        "ema20": ema20_value,
        "ema50": ema50_value,
        "ema200": ema200_value,

        "rsi": current_rsi,
        "atr": current_atr,
        "adx": current_adx,

        "rel_volume": rel_volume,

        "resistance20": resistance20,
        "support20": support20,

        "high52": high52,
        "low52": low52,

        "breakout20": breakout20,
        "near_breakout": near_breakout,
        "breakout52": breakout52,

        "macd_bull": macd_bull,
        "macd_rising": macd_rising,

        "bullish_candle": bullish_candle,
        "strong_bullish_candle": strong_bullish_candle,
        "bearish_candle": bearish_candle,
        "candle": candle,

        "overextended": overextended,
        "distance_ema20": distance_from_ema20,

        "daily_score": daily_score
    }


# ============================================================
# HOURLY ANALYSIS
# ============================================================

def analyze_hourly(df):

    df = clean_yf_dataframe(
        df
    )

    if (
        df is None
        or
        len(df) < MIN_HOURLY_BARS
    ):
        return None

    close = df["Close"]

    ema20 = close.ewm(
        span=20,
        adjust=False
    ).mean()

    ema50 = close.ewm(
        span=50,
        adjust=False
    ).mean()

    r = rsi(
        close
    )

    adx_value = adx(
        df
    )

    price = safe_float(
        close.iloc[-1]
    )

    current_rsi = safe_float(
        r.iloc[-1]
    )

    current_adx = safe_float(
        adx_value.iloc[-1]
    )

    ema20_now = safe_float(
        ema20.iloc[-1]
    )

    ema50_now = safe_float(
        ema50.iloc[-1]
    )

    above20 = (
        price >
        ema20_now
    )

    above50 = (
        price >
        ema50_now
    )

    stack = (
        above20
        and
        above50
        and
        ema20_now >
        ema50_now
    )

    momentum = (
        50 <= current_rsi <= 75
    )

    trend = (
        ema20.iloc[-1] >
        ema20.iloc[-6]
        and
        ema50.iloc[-1] >
        ema50.iloc[-6]
    )

    adx_good = (
        current_adx >= 18
    )

    # 1H local structure
    recent_high = safe_float(
        df["High"]
        .iloc[-21:-1]
        .max()
    )

    recent_low = safe_float(
        df["Low"]
        .iloc[-21:-1]
        .min()
    )

    breakout = (
        price >
        recent_high
    )

    candle = candle_pattern(
        df
    )

    bullish_candle = candle in [
        "Bullish Engulfing",
        "Hammer",
        "Bullish Candle"
    ]

    hourly_score = 0

    hourly_score += 5 if above20 else 0
    hourly_score += 5 if above50 else 0
    hourly_score += 5 if stack else 0
    hourly_score += 5 if momentum else 0
    hourly_score += 5 if trend else 0
    hourly_score += 5 if adx_good else 0

    hourly_score = min(
        30,
        hourly_score
    )

    return {

        "price": price,

        "rsi": current_rsi,
        "adx": current_adx,

        "above20": above20,
        "above50": above50,
        "stack": stack,

        "momentum": momentum,
        "trend": trend,
        "adx_good": adx_good,

        "recent_high": recent_high,
        "recent_low": recent_low,

        "breakout": breakout,

        "candle": candle,
        "bullish_candle": bullish_candle,

        "hourly_score": hourly_score
    }


# ============================================================
# 15 MINUTE ANALYSIS
# ============================================================

def analyze_15m(df):

    df = clean_yf_dataframe(
        df
    )

    if (
        df is None
        or
        len(df) < MIN_15M_BARS
    ):
        return None

    close = df["Close"]

    volume = (
        df["Volume"]
        .replace(
            0,
            np.nan
        )
    )

    ema9 = close.ewm(
        span=9,
        adjust=False
    ).mean()

    ema20 = close.ewm(
        span=20,
        adjust=False
    ).mean()

    r = rsi(
        close
    )

    atr_value = atr(
        df
    )

    vol20 = volume.rolling(
        20
    ).mean()

    price = safe_float(
        close.iloc[-1]
    )

    current_rsi = safe_float(
        r.iloc[-1]
    )

    current_atr = safe_float(
        atr_value.iloc[-1]
    )

    current_vol = safe_float(
        volume.iloc[-1]
    )

    avg_vol = safe_float(
        vol20.iloc[-1]
    )

    if avg_vol > 0:

        rel_volume = (
            current_vol /
            avg_vol
        )

    else:

        rel_volume = 0

    ema9_now = safe_float(
        ema9.iloc[-1]
    )

    ema20_now = safe_float(
        ema20.iloc[-1]
    )

    above9 = (
        price >
        ema9_now
    )

    above20 = (
        price >
        ema20_now
    )

    momentum = (
        50 <= current_rsi <= 75
    )

    volume_expansion = (
        rel_volume >= 1.15
    )

    strong_volume = (
        rel_volume >= 1.40
    )

    recent_high = safe_float(
        df["High"]
        .iloc[-11:-1]
        .max()
    )

    recent_low = safe_float(
        df["Low"]
        .iloc[-11:-1]
        .min()
    )

    micro_breakout = (
        price >
        recent_high
    )

    candle = candle_pattern(
        df
    )

    bullish_candle = candle in [
        "Bullish Engulfing",
        "Hammer",
        "Bullish Candle"
    ]

    strong_bullish_candle = candle in [
        "Bullish Engulfing",
        "Hammer"
    ]

    # 15M entry confirmation
    entry_confirmation = (
        above9
        and
        above20
        and
        momentum
        and
        (
            micro_breakout
            or
            strong_bullish_candle
        )
    )

    score = 0

    score += 5 if above9 else 0
    score += 5 if above20 else 0
    score += 4 if momentum else 0
    score += 4 if volume_expansion else 0
    score += 5 if micro_breakout else 0
    score += 7 if bullish_candle else 0

    score = min(
        30,
        score
    )

    return {

        "price": price,

        "rsi": current_rsi,
        "atr": current_atr,

        "rel_volume": rel_volume,

        "above9": above9,
        "above20": above20,

        "momentum": momentum,
        "volume_expansion": volume_expansion,
        "strong_volume": strong_volume,

        "micro_breakout": micro_breakout,

        "bullish_candle": bullish_candle,
        "strong_bullish_candle": strong_bullish_candle,
        "candle": candle,

        "entry_confirmation": entry_confirmation,

        "recent_high": recent_high,
        "recent_low": recent_low,

        "score": score
    }


# ============================================================
# SECTOR STRENGTH
# ============================================================

def calculate_sector_strength(
    daily_cache
):

    sector_scores = {}

    for sector in SECTOR_MAP:

        scores = []

        for symbol, data in daily_cache.items():

            if data is None:
                continue

            if get_sector(symbol) != sector:
                continue

            scores.append(
                data["daily_score"]
            )

        if scores:

            sector_scores[sector] = float(
                np.mean(scores)
            )

        else:

            sector_scores[sector] = 0.0

    # Other sector
    other_scores = []

    for symbol, data in daily_cache.items():

        if data is None:
            continue

        if get_sector(symbol) == "Other":

            other_scores.append(
                data["daily_score"]
            )

    sector_scores["Other"] = (
        float(
            np.mean(other_scores)
        )
        if other_scores
        else 0.0
    )

    return sector_scores


# ============================================================
# TRADE PLAN
# ============================================================

def create_trade_plan(
    daily,
    hourly,
    m15
):

    if (
        daily is None
        or
        hourly is None
        or
        m15 is None
    ):
        return None

    price = daily["price"]

    atr_value = max(
        daily["atr"],
        0.00001
    )

    daily_resistance = (
        daily["resistance20"]
    )

    daily_support = (
        daily["support20"]
    )

    hourly_support = (
        hourly.get(
            "recent_low",
            daily_support
        )
    )

    m15_support = (
        m15.get(
            "recent_low",
            hourly_support
        )
    )

    # ========================================================
    # ENTRY
    # ========================================================

    # For breakout:
    # do not blindly use resistance + 0.2% if price is
    # already far above it.
    if daily["breakout20"]:

        entry = max(
            price,
            daily_resistance
        )

    elif daily["near_breakout"]:

        entry = max(
            price,
            daily_resistance * 1.001
        )

    else:

        entry = price

    # 15M breakout confirmation
    micro_high = m15.get(
        "recent_high",
        0
    )

    if (
        micro_high > 0
        and
        micro_high <=
        entry * 1.015
    ):

        if m15["micro_breakout"]:

            entry = max(
                entry,
                micro_high
            )

    # ========================================================
    # STRUCTURAL STOP
    # ========================================================

    support_candidates = [
        x
        for x in [
            daily_support,
            hourly_support,
            m15_support
        ]
        if x > 0
        and x < entry
    ]

    if support_candidates:

        structural_support = max(
            support_candidates
        )

    else:

        structural_support = (
            entry -
            1.5 * atr_value
        )

    atr_stop = (
        entry -
        1.5 * atr_value
    )

    structure_stop = (
        structural_support -
        0.15 * atr_value
    )

    # Use the wider/safer stop
    sl = min(
        atr_stop,
        structure_stop
    )

    if sl >= entry:

        sl = (
            entry -
            1.5 * atr_value
        )

    risk = (
        entry -
        sl
    )

    if risk <= 0:
        return None

    # ========================================================
    # TARGETS
    # ========================================================

    tp1 = (
        entry +
        2.0 * risk
    )

    tp2 = (
        entry +
        3.0 * risk
    )

    rr1 = (
        tp1 -
        entry
    ) / risk

    rr2 = (
        tp2 -
        entry
    ) / risk

    if rr1 < 2:
        return None

    # Reject absurdly wide risk
    risk_pct = (
        risk /
        max(
            entry,
            0.00001
        )
    ) * 100

    if risk_pct > 12:
        return None

    return {

        "entry": entry,
        "sl": sl,

        "tp1": tp1,
        "tp2": tp2,

        "rr1": rr1,
        "rr2": rr2,

        "risk_pct": risk_pct
    }


# ============================================================
# GRADE
# ============================================================

def final_grade(
    quality_score
):

    if quality_score >= 88:
        return "A+"

    if quality_score >= 78:
        return "A"

    if quality_score >= 68:
        return "B"

    return "C"


# ============================================================
# FINAL CANDIDATE ANALYSIS
# ============================================================

def analyze_candidate(
    symbol,
    daily,
    hourly,
    m15,
    sector_strength,
    regime,
    strict_market=True
):

    if daily is None:
        return None

    if hourly is None:
        return None

    if m15 is None:
        return None

    # ========================================================
    # MARKET REGIME FILTER
    # ========================================================

    if strict_market:

        if regime == "BEARISH":

            if daily["daily_score"] < 30:
                return None

            if hourly["hourly_score"] < 23:
                return None

        elif regime == "SIDEWAYS":

            if daily["daily_score"] < 27:
                return None

            if hourly["hourly_score"] < 21:
                return None

        elif regime == "BULLISH":

            if daily["daily_score"] < 25:
                return None

    # ========================================================
    # BASIC QUALITY CONDITIONS
    # ========================================================

    if daily["overextended"]:
        return None

    if daily["rel_volume"] < 1.15:
        return None

    if daily["rsi"] < 50:
        return None

    if hourly["rsi"] < 48:
        return None

    if not daily["macd_bull"]:
        return None

    # ========================================================
    # SECTOR
    # ========================================================

    sector = get_sector(
        symbol
    )

    sector_raw = sector_strength.get(
        sector,
        0
    )

    sector_score = min(
        10,
        max(
            0,
            (
                sector_raw /
                40
            ) * 10
        )
    )

    # ========================================================
    # SCORES
    # ========================================================

    daily_score = (
        daily["daily_score"]
    )

    hourly_score = (
        hourly["hourly_score"]
    )

    m15_score = (
        m15["score"]
    )

    # ========================================================
    # TREND
    # ========================================================

    trend_ok = (
        daily_score >= 25
        and
        hourly_score >= 20
        and
        daily["ema20"] >
        daily["ema50"]
        and
        daily["ema50"] >
        daily["ema200"]
    )

    # ========================================================
    # MOMENTUM
    # ========================================================

    momentum_ok = (
        daily["rsi"] >= 52
        and
        daily["rsi"] <= 72
        and
        hourly["rsi"] >= 50
        and
        hourly["rsi"] <= 75
        and
        daily["adx"] >= 18
    )

    # ========================================================
    # BREAKOUT
    # ========================================================

    breakout_ok = (
        daily["breakout20"]
        or
        daily["near_breakout"]
        or
        daily["breakout52"]
        or
        hourly["breakout"]
        or
        m15["micro_breakout"]
    )

    # ========================================================
    # VOLUME
    # ========================================================

    volume_ok = (
        daily["rel_volume"] >= 1.20
        or
        (
            daily["rel_volume"] >= 1.10
            and
            m15["rel_volume"] >= 1.30
        )
    )

    # ========================================================
    # PRICE ACTION
    # ========================================================

    price_action_ok = (
        daily["bullish_candle"]
        or
        hourly["bullish_candle"]
        or
        m15["bullish_candle"]
    )

    # ========================================================
    # ENTRY CONFIRMATION
    # ========================================================

    entry_confirmed = (
        m15["entry_confirmation"]
    )

    # ========================================================
    # TRADE PLAN
    # ========================================================

    trade = create_trade_plan(
        daily,
        hourly,
        m15
    )

    if trade is None:
        return None

    # ========================================================
    # QUALITY SCORE / 100
    #
    # Components:
    #
    # Trend             20
    # Momentum          15
    # Breakout          15
    # Volume            10
    # Sector            10
    # Price Action      10
    # MTF Confirmation  10
    # Risk/Reward       10
    # ========================================================

    quality = 0.0

    # --------------------------------------------------------
    # TREND 20
    # --------------------------------------------------------

    trend_component = (
        daily_score /
        40
    ) * 20

    quality += trend_component

    # --------------------------------------------------------
    # MOMENTUM 15
    # --------------------------------------------------------

    momentum_component = 0

    if daily["rsi"] >= 52:
        momentum_component += 4

    if (
        55 <=
        daily["rsi"] <=
        68
    ):
        momentum_component += 2

    if daily["macd_bull"]:
        momentum_component += 3

    if daily["macd_rising"]:
        momentum_component += 2

    if daily["adx"] >= 20:
        momentum_component += 4

    quality += min(
        15,
        momentum_component
    )

    # --------------------------------------------------------
    # BREAKOUT 15
    # --------------------------------------------------------

    breakout_component = 0

    if daily["breakout20"]:
        breakout_component += 6

    elif daily["near_breakout"]:
        breakout_component += 4

    if daily["breakout52"]:
        breakout_component += 4

    if hourly["breakout"]:
        breakout_component += 2

    if m15["micro_breakout"]:
        breakout_component += 3

    quality += min(
        15,
        breakout_component
    )

    # --------------------------------------------------------
    # VOLUME 10
    # --------------------------------------------------------

    volume_component = min(
        7,
        daily["rel_volume"] * 4
    )

    if m15["rel_volume"] >= 1.30:
        volume_component += 3

    quality += min(
        10,
        volume_component
    )

    # --------------------------------------------------------
    # SECTOR 10
    # --------------------------------------------------------

    quality += sector_score

    # --------------------------------------------------------
    # PRICE ACTION 10
    # --------------------------------------------------------

    pa_component = 0

    if daily["strong_bullish_candle"]:
        pa_component += 4

    elif daily["bullish_candle"]:
        pa_component += 3

    if hourly["bullish_candle"]:
        pa_component += 2

    if m15["strong_bullish_candle"]:
        pa_component += 4

    elif m15["bullish_candle"]:
        pa_component += 3

    quality += min(
        10,
        pa_component
    )

    # --------------------------------------------------------
    # MTF CONFIRMATION 10
    # --------------------------------------------------------

    mtf_component = 0

    if daily_score >= 28:
        mtf_component += 3

    elif daily_score >= 25:
        mtf_component += 2

    if hourly_score >= 24:
        mtf_component += 3

    elif hourly_score >= 20:
        mtf_component += 2

    if m15_score >= 24:
        mtf_component += 4

    elif m15_score >= 20:
        mtf_component += 3

    quality += min(
        10,
        mtf_component
    )

    # --------------------------------------------------------
    # R:R 10
    # --------------------------------------------------------

    rr_component = min(
        10,
        trade["rr2"] * 3.0
    )

    quality += rr_component

    # ========================================================
    # PENALTIES
    # ========================================================

    if daily["overextended"]:

        quality -= 15

    if not volume_ok:

        quality -= 7

    if not breakout_ok:

        quality -= 5

    if not price_action_ok:

        quality -= 4

    if regime == "BEARISH":

        quality -= 10

    elif regime == "SIDEWAYS":

        quality -= 4

    # Small penalty for excessive risk
    if trade["risk_pct"] > 8:

        quality -= 4

    quality = max(
        0,
        min(
            100,
            quality
        )
    )

    # ========================================================
    # HARD FILTERS
    # ========================================================

    if quality < 65:
        return None

    if not trend_ok:
        return None

    if not momentum_ok:
        return None

    if not volume_ok:
        return None

    if daily["overextended"]:
        return None

    if trade["rr1"] < 2:
        return None

    # 15M should either confirm or be very close
    if (
        not entry_confirmed
        and
        m15_score < 20
    ):
        return None

    # Breakout/trend setup must have structure
    if not breakout_ok:
        return None

    # ========================================================
    # GRADE
    # ========================================================

    grade = final_grade(
        quality
    )

    # ========================================================
    # SETUP TYPE
    # ========================================================

    if (
        daily["breakout20"]
        and
        hourly["breakout"]
        and
        m15["micro_breakout"]
    ):

        setup_type = (
            "Triple-Timeframe Breakout"
        )

    elif (
        daily["breakout20"]
        and
        m15["micro_breakout"]
    ):

        setup_type = (
            "Confirmed Breakout"
        )

    elif (
        daily["near_breakout"]
        and
        m15["micro_breakout"]
    ):

        setup_type = (
            "Breakout Continuation"
        )

    elif (
        daily["ema20"] >
        daily["ema50"]
        and
        hourly["bullish_candle"]
        and
        m15["bullish_candle"]
    ):

        setup_type = (
            "Trend Pullback"
        )

    else:

        setup_type = (
            "Momentum Continuation"
        )

    # ========================================================
    # REASONS
    # ========================================================

    reasons = []

    if (
        daily["ema20"] >
        daily["ema50"]
    ):
        reasons.append(
            "EMA20 > EMA50"
        )

    if (
        daily["ema50"] >
        daily["ema200"]
    ):
        reasons.append(
            "EMA50 > EMA200"
        )

    if daily["breakout20"]:

        reasons.append(
            "20D breakout"
        )

    elif daily["near_breakout"]:

        reasons.append(
            "Near 20D breakout"
        )

    if daily["breakout52"]:

        reasons.append(
            "52W strength"
        )

    if daily["rel_volume"] >= 1.50:

        reasons.append(
            "Strong volume"
        )

    elif daily["rel_volume"] >= 1.20:

        reasons.append(
            "Volume expansion"
        )

    if daily["strong_bullish_candle"]:

        reasons.append(
            daily["candle"]
        )

    elif daily["bullish_candle"]:

        reasons.append(
            daily["candle"]
        )

    if hourly["stack"]:

        reasons.append(
            "1H trend confirmation"
        )

    if hourly["breakout"]:

        reasons.append(
            "1H breakout"
        )

    if m15["micro_breakout"]:

        reasons.append(
            "15M breakout"
        )

    if m15["strong_bullish_candle"]:

        reasons.append(
            "15M price action"
        )

    if m15["rel_volume"] >= 1.30:

        reasons.append(
            "15M volume expansion"
        )

    reason_text = " • ".join(
        reasons[:9]
    )

    return {

        "Ticker": symbol.replace(
            ".NS",
            ""
        ),

        "Sector": sector,

        "Setup": setup_type,

        "Grade": grade,

        "Quality": round(
            quality,
            1
        ),

        "Price": round(
            daily["price"],
            2
        ),

        "Entry": round(
            trade["entry"],
            2
        ),

        "SL": round(
            trade["sl"],
            2
        ),

        "TP1": round(
            trade["tp1"],
            2
        ),

        "TP2": round(
            trade["tp2"],
            2
        ),

        "R:R": (
            f"1:{trade['rr1']:.1f}"
        ),

        "Risk %": round(
            trade["risk_pct"],
            2
        ),

        "Daily": round(
            daily_score,
            1
        ),

        "1H": round(
            hourly_score,
            1
        ),

        "15M": round(
            m15_score,
            1
        ),

        "RSI": round(
            daily["rsi"],
            1
        ),

        "Vol ×": round(
            daily["rel_volume"],
            2
        ),

        "15M Vol ×": round(
            m15["rel_volume"],
            2
        ),

        "ADX": round(
            daily["adx"],
            1
        ),

        "Candle": daily["candle"],

        "20D Breakout": (
            "YES"
            if daily["breakout20"]
            else "NO"
        ),

        "52W Breakout": (
            "YES"
            if daily["breakout52"]
            else "NO"
        ),

        "Market": regime,

        "Reason": reason_text
    }


# ============================================================
# SINGLE STOCK DOWNLOAD
# ============================================================

@st.cache_data(
    ttl=CACHE_TTL_DAILY,
    show_spinner=False
)
def download_stock(
    symbol,
    period,
    interval
):

    try:

        data = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False
        )

        return clean_yf_dataframe(
            data
        )

    except Exception:

        return None


# ============================================================
# PARALLEL DOWNLOAD HELPER
# ============================================================

def parallel_download(
    symbols,
    period,
    interval,
    max_workers
):

    results = {}

    if not symbols:
        return results

    def fetch(symbol):

        try:

            return (
                symbol,
                download_stock(
                    symbol,
                    period,
                    interval
                )
            )

        except Exception:

            return (
                symbol,
                None
            )

    workers = min(
        max_workers,
        max(
            1,
            len(symbols)
        )
    )

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = [
            executor.submit(
                fetch,
                symbol
            )
            for symbol in symbols
        ]

        for future in as_completed(
            futures
        ):

            try:

                symbol, data = (
                    future.result()
                )

                results[
                    symbol
                ] = data

            except Exception:

                pass

    # Preserve input order
    return {
        symbol: results.get(
            symbol
        )
        for symbol in symbols
    }


# ============================================================
# CHART
# ============================================================

def show_chart(
    symbol,
    period="1y"
):

    df = download_stock(
        symbol,
        period,
        "1d"
    )

    if df is None:

        st.warning(
            "Chart unavailable."
        )

        return

    chart = df[
        ["Close"]
    ].copy()

    chart["EMA20"] = (
        chart["Close"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    chart["EMA50"] = (
        chart["Close"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )

    chart["EMA200"] = (
        chart["Close"]
        .ewm(
            span=200,
            adjust=False
        )
        .mean()
    )

    st.line_chart(
        chart
    )


# ============================================================
# HEADER
# ============================================================

regime = market_regime()

st.title(
    "🔥 Vardha Pro Stock Screener V5.1"
)

st.caption(
    "Optimized Best-of-the-Best Multi-Timeframe Setup Engine"
)

st.caption(
    f"NIFTY Universe: {len(SYMBOLS)} symbols • "
    f"Market Regime: {regime}"
)

st.warning(
    "Educational/research tool only. "
    "Quality scores are rule-based technical rankings "
    "and are NOT guaranteed probabilities of profit."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ V5.1 Settings"
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
            "Symbols",
            "RELIANCE, TCS, INFY, HDFCBANK"
        )

        selected = [
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
            x if x.endswith(".NS")
            else x + ".NS"
            for x in selected
        ]

    else:

        scan_symbols = SYMBOLS

    st.header(
        "🏆 Results"
    )

    top_n = st.slider(
        "Show Top Setups",
        TOP_MIN,
        TOP_MAX,
        10
    )

    st.header(
        "🏦 Sector"
    )

    sector_filter = st.selectbox(
        "Sector filter",
        [
            "All sectors"
        ] +
        list(
            SECTOR_MAP.keys()
        )
    )

    if sector_filter != "All sectors":

        allowed = SECTOR_MAP.get(
            sector_filter,
            set()
        )

        scan_symbols = [
            symbol
            for symbol in scan_symbols
            if symbol.replace(
                ".NS",
                ""
            ).upper()
            in allowed
        ]

    st.header(
        "🛡️ Market Filter"
    )

    strict_market = st.checkbox(
        "Strict market regime",
        True
    )

    st.header(
        "🔎 Individual Stock"
    )

    search_stock = st.text_input(
        "Search",
        placeholder="RELIANCE"
    )

    scan_button = st.button(
        "🚀 SCAN BEST SETUPS",
        type="primary",
        use_container_width=True
    )


# ============================================================
# SCAN
# ============================================================

if scan_button:

    start_time = datetime.now()

    progress = st.progress(
        0.0
    )

    status = st.empty()

    # --------------------------------------------------------
    # PASS 1 — DAILY DATA
    # --------------------------------------------------------

    status.write(
        f"📅 Downloading Daily data for "
        f"{len(scan_symbols)} stocks..."
    )

    daily_data = parallel_download(
        scan_symbols,
        "2y",
        "1d",
        MAX_WORKERS_DAILY
    )

    progress.progress(
        0.30
    )

    # --------------------------------------------------------
    # DAILY ANALYSIS
    # --------------------------------------------------------

    status.write(
        "📊 Analysing Daily trend, momentum, "
        "breakout and volume..."
    )

    daily_cache = {}

    for symbol in scan_symbols:

        daily_cache[
            symbol
        ] = analyze_daily(
            daily_data.get(
                symbol
            )
        )

    # --------------------------------------------------------
    # SECTOR STRENGTH
    # --------------------------------------------------------

    sector_strength = (
        calculate_sector_strength(
            daily_cache
        )
    )

    progress.progress(
        0.42
    )

    # --------------------------------------------------------
    # DAILY PRE-FILTER
    # --------------------------------------------------------

    candidates = []

    for symbol, daily in daily_cache.items():

        if daily is None:
            continue

        # Market-sensitive threshold
        if regime == "BULLISH":

            minimum_daily = 23

        elif regime == "SIDEWAYS":

            minimum_daily = 26

        elif regime == "BEARISH":

            minimum_daily = 29

        else:

            minimum_daily = 25

        if strict_market:

            minimum_daily = max(
                minimum_daily,
                25
            )

        if (
            daily["daily_score"] <
            minimum_daily
        ):
            continue

        # Reject obvious chasing
        if daily["overextended"]:
            continue

        # Minimum volume
        if daily["rel_volume"] < 1.05:
            continue

        # Need either breakout strength or
        # strong trend structure
        structure_ok = (
            daily["breakout20"]
            or
            daily["near_breakout"]
            or
            daily["breakout52"]
            or
            (
                daily["ema20"] >
                daily["ema50"] >
                daily["ema200"]
            )
        )

        if not structure_ok:
            continue

        candidates.append(
            symbol
        )

    # --------------------------------------------------------
    # RANK DAILY CANDIDATES
    # --------------------------------------------------------

    candidates = sorted(
        candidates,
        key=lambda symbol: (
            daily_cache[symbol][
                "daily_score"
            ],
            daily_cache[symbol][
                "rel_volume"
            ],
            daily_cache[symbol][
                "adx"
            ]
        ),
        reverse=True
    )

    # Limit expensive intraday requests
    candidates = candidates[
        :MAX_DAILY_PREFILTER
    ]

    candidates = candidates[
        :MAX_INTRADAY_CANDIDATES
    ]

    progress.progress(
        0.45
    )

    # --------------------------------------------------------
    # PASS 2 — 1H
    # --------------------------------------------------------

    status.write(
        f"⏱️ Downloading 1H confirmation "
        f"for {len(candidates)} candidates..."
    )

    hourly_data = parallel_download(
        candidates,
        "60d",
        "1h",
        MAX_WORKERS_INTRADAY
    )

    progress.progress(
        0.62
    )

    hourly_cache = {}

    for symbol in candidates:

        hourly_cache[
            symbol
        ] = analyze_hourly(
            hourly_data.get(
                symbol
            )
        )

    # --------------------------------------------------------
    # HOURLY PRE-FILTER
    # --------------------------------------------------------

    hourly_candidates = []

    for symbol in candidates:

        hourly = hourly_cache.get(
            symbol
        )

        daily = daily_cache.get(
            symbol
        )

        if hourly is None:
            continue

        if daily is None:
            continue

        if hourly["hourly_score"] < 18:
            continue

        # Stronger 1H requirement in weak markets
        if (
            strict_market
            and
            regime == "BEARISH"
            and
            hourly["hourly_score"] < 23
        ):
            continue

        if (
            not hourly["stack"]
            and
            not hourly["breakout"]
        ):
            continue

        hourly_candidates.append(
            symbol
        )

    # --------------------------------------------------------
    # PASS 3 — 15M
    # --------------------------------------------------------

    status.write(
        f"⚡ Downloading 15M entry data "
        f"for {len(hourly_candidates)} candidates..."
    )

    m15_data = parallel_download(
        hourly_candidates,
        "30d",
        "15m",
        MAX_WORKERS_INTRADAY
    )

    progress.progress(
        0.82
    )

    m15_cache = {}

    for symbol in hourly_candidates:

        m15_cache[
            symbol
        ] = analyze_15m(
            m15_data.get(
                symbol
            )
        )

    # --------------------------------------------------------
    # FINAL ANALYSIS
    # --------------------------------------------------------

    status.write(
        "🏆 Calculating final quality scores..."
    )

    final_results = []

    for symbol in hourly_candidates:

        result = analyze_candidate(
            symbol,
            daily_cache.get(
                symbol
            ),
            hourly_cache.get(
                symbol
            ),
            m15_cache.get(
                symbol
            ),
            sector_strength,
            regime,
            strict_market
        )

        if result is not None:

            final_results.append(
                result
            )

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    result_df = pd.DataFrame(
        final_results
    )

    if not result_df.empty:

        grade_order = {
            "A+": 0,
            "A": 1,
            "B": 2,
            "C": 3
        }

        result_df["GradeOrder"] = (
            result_df["Grade"]
            .map(
                grade_order
            )
            .fillna(9)
        )

        # Final ranking is primarily Quality,
        # then Grade, then multi-timeframe strength.
        result_df = (
            result_df
            .sort_values(
                [
                    "GradeOrder",
                    "Quality",
                    "Daily",
                    "1H",
                    "15M",
                    "Vol ×",
                    "ADX"
                ],
                ascending=[
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False
                ]
            )
            .reset_index(
                drop=True
            )
        )

        result_df.insert(
            0,
            "Rank",
            np.arange(
                1,
                len(result_df) + 1
            )
        )

        result_df = (
            result_df
            .drop(
                columns=[
                    "GradeOrder"
                ],
                errors="ignore"
            )
        )

    # --------------------------------------------------------
    # FINISH
    # --------------------------------------------------------

    progress.progress(
        1.0
    )

    elapsed = (
        datetime.now() -
        start_time
    ).total_seconds()

    status.empty()
    progress.empty()

    # --------------------------------------------------------
    # SESSION STATE
    # --------------------------------------------------------

    st.session_state[
        "v51_results"
    ] = result_df

    st.session_state[
        "v51_scanned"
    ] = len(
        scan_symbols
    )

    st.session_state[
        "v51_daily_candidates"
    ] = len(
        candidates
    )

    st.session_state[
        "v51_hourly_candidates"
    ] = len(
        hourly_candidates
    )

    st.session_state[
        "v51_scan_time"
    ] = round(
        elapsed,
        1
    )

    st.session_state[
        "v51_sector_strength"
    ] = sector_strength

    st.session_state[
        "v51_regime"
    ] = regime


# ============================================================
# RESULTS
# ============================================================

if "v51_results" not in st.session_state:

    st.info(
        "Configure the filters and press "
        "🚀 SCAN BEST SETUPS."
    )

else:

    df = st.session_state[
        "v51_results"
    ]

    scanned = st.session_state.get(
        "v51_scanned",
        0
    )

    daily_candidates = (
        st.session_state.get(
            "v51_daily_candidates",
            0
        )
    )

    hourly_candidates = (
        st.session_state.get(
            "v51_hourly_candidates",
            0
        )
    )

    scan_time = (
        st.session_state.get(
            "v51_scan_time",
            0
        )
    )

    stored_regime = (
        st.session_state.get(
            "v51_regime",
            regime
        )
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    st.subheader(
        "🏆 BEST-OF-THE-BEST V5.1 SETUPS"
    )

    if df is None or df.empty:

        st.error(
            "No setup passed the strict V5.1 filters."
        )

        st.write(
            "This means the engine did not find a setup "
            "strong enough to meet the current trend, "
            "momentum, volume, breakout, MTF and risk/reward "
            "requirements."
        )

    else:

        aplus = int(
            (
                df["Grade"] ==
                "A+"
            ).sum()
        )

        agrade = int(
            (
                df["Grade"] ==
                "A"
            ).sum()
        )

        avg_quality = round(
            df["Quality"].mean(),
            1
        )

        best_quality = round(
            df["Quality"].max(),
            1
        )

        c1, c2, c3, c4, c5, c6 = st.columns(
            6
        )

        c1.metric(
            "🔎 Scanned",
            scanned
        )

        c2.metric(
            "📅 Daily Shortlist",
            daily_candidates
        )

        c3.metric(
            "⏱️ 1H Shortlist",
            hourly_candidates
        )

        c4.metric(
            "🔥 A+ Setups",
            aplus
        )

        c5.metric(
            "⭐ Best Quality",
            f"{best_quality}/100"
        )

        c6.metric(
            "⚡ Scan Time",
            f"{scan_time}s"
        )

        st.caption(
            f"Market Regime: {stored_regime} • "
            f"Average Quality: {avg_quality}/100"
        )

        # ====================================================
        # TOP N
        # ====================================================

        top = df.head(
            top_n
        ).copy()

        st.subheader(
            f"🥇 TOP {len(top)} RANKED SETUPS"
        )

        display_cols = [
            "Rank",
            "Ticker",
            "Sector",
            "Setup",
            "Grade",
            "Quality",
            "Price",
            "Entry",
            "SL",
            "TP1",
            "TP2",
            "R:R",
            "Risk %",
            "Daily",
            "1H",
            "15M",
            "RSI",
            "Vol ×",
            "ADX"
        ]

        st.dataframe(
            top[
                display_cols
            ],
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # BEST SETUP
        # ====================================================

        best = top.iloc[0]

        st.subheader(
            f"🥇 #1 BEST SETUP — "
            f"{best['Ticker']}"
        )

        b1, b2, b3, b4, b5, b6 = st.columns(
            6
        )

        b1.metric(
            "Grade",
            best["Grade"]
        )

        b2.metric(
            "Quality",
            f"{best['Quality']}/100"
        )

        b3.metric(
            "Entry",
            f"₹{best['Entry']}"
        )

        b4.metric(
            "SL",
            f"₹{best['SL']}"
        )

        b5.metric(
            "TP1",
            f"₹{best['TP1']}"
        )

        b6.metric(
            "R:R",
            best["R:R"]
        )

        st.success(
            f"**{best['Setup']}** • "
            f"{best['Reason']}"
        )

        # ====================================================
        # TABS
        # ====================================================

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "🏆 Top Setups",
                "📊 All Ranked",
                "🎯 Trade Plans",
                "🏦 Sector Strength",
                "📘 V5.1 Engine"
            ]
        )

        # ====================================================
        # TOP SETUPS
        # ====================================================

        with tab1:

            for _, row in top.iterrows():

                with st.expander(
                    f"#{int(row['Rank'])} "
                    f"{row['Ticker']} — "
                    f"{row['Grade']} — "
                    f"{row['Quality']}/100"
                ):

                    x1, x2, x3, x4, x5 = st.columns(
                        5
                    )

                    x1.metric(
                        "Entry",
                        f"₹{row['Entry']}"
                    )

                    x2.metric(
                        "Stop Loss",
                        f"₹{row['SL']}"
                    )

                    x3.metric(
                        "TP1",
                        f"₹{row['TP1']}"
                    )

                    x4.metric(
                        "TP2",
                        f"₹{row['TP2']}"
                    )

                    x5.metric(
                        "R:R",
                        row["R:R"]
                    )

                    st.write(
                        f"**Setup:** {row['Setup']}"
                    )

                    st.write(
                        f"**Sector:** {row['Sector']}"
                    )

                    st.write(
                        f"**Grade:** {row['Grade']} | "
                        f"**Quality:** {row['Quality']}/100"
                    )

                    st.write(
                        f"**Daily:** {row['Daily']}/40 | "
                        f"**1H:** {row['1H']}/30 | "
                        f"**15M:** {row['15M']}/30"
                    )

                    st.write(
                        f"**RSI:** {row['RSI']} | "
                        f"**Daily Volume:** {row['Vol ×']}× | "
                        f"**15M Volume:** {row['15M Vol ×']}× | "
                        f"**ADX:** {row['ADX']}"
                    )

                    st.write(
                        f"**Risk:** {row['Risk %']}%"
                    )

                    st.write(
                        f"**Reason:** {row['Reason']}"
                    )

        # ====================================================
        # ALL RANKED
        # ====================================================

        with tab2:

            all_cols = [
                "Rank",
                "Ticker",
                "Sector",
                "Setup",
                "Grade",
                "Quality",
                "Price",
                "Entry",
                "SL",
                "TP1",
                "TP2",
                "R:R",
                "Risk %",
                "Daily",
                "1H",
                "15M",
                "RSI",
                "Vol ×",
                "15M Vol ×",
                "ADX",
                "Candle",
                "20D Breakout",
                "52W Breakout",
                "Market"
            ]

            st.dataframe(
                df[
                    all_cols
                ],
                use_container_width=True,
                hide_index=True
            )

            csv_data = (
                df
                .to_csv(
                    index=False
                )
                .encode(
                    "utf-8"
                )
            )

            st.download_button(
                "⬇️ Download V5.1 Ranked CSV",
                csv_data,
                "vardha_pro_screener_v5_1.csv",
                "text/csv"
            )

        # ====================================================
        # TRADE PLANS
        # ====================================================

        with tab3:

            plan_cols = [
                "Rank",
                "Ticker",
                "Grade",
                "Quality",
                "Setup",
                "Entry",
                "SL",
                "TP1",
                "TP2",
                "R:R",
                "Risk %"
            ]

            st.dataframe(
                df.head(
                    top_n
                )[
                    plan_cols
                ],
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Entry, SL and targets are rule-based "
                "research levels and may differ from "
                "actual execution prices."
            )

        # ====================================================
        # SECTOR STRENGTH
        # ====================================================

        with tab4:

            sector_data = (
                st.session_state.get(
                    "v51_sector_strength",
                    {}
                )
            )

            if sector_data:

                sector_df = pd.DataFrame(
                    [
                        {
                            "Sector": sector,
                            "Strength": round(
                                value,
                                1
                            )
                        }
                        for sector, value
                        in sector_data.items()
                    ]
                ).sort_values(
                    "Strength",
                    ascending=False
                )

                st.dataframe(
                    sector_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "Sector strength unavailable."
                )

        # ====================================================
        # ENGINE
        # ====================================================

        with tab5:

            st.markdown(
                """
# 🔥 Vardha Pro Stock Screener V5.1

## ⚡ Optimized Pipeline

### STEP 1 — NIFTY 500

The engine starts with the NIFTY 500 universe.

---

### STEP 2 — Daily Selection

Every stock is evaluated for:

- EMA20
- EMA50
- EMA200
- EMA stacking
- RSI
- MACD
- MACD direction
- ADX
- 20-day breakout
- 52-week strength
- Relative volume
- Price action
- Trend slope
- ATR-based overextension

**Maximum Daily Score = 40**

Weak stocks are rejected before expensive intraday analysis.

---

### STEP 3 — 1H Confirmation

The remaining candidates are checked for:

- EMA20
- EMA50
- Trend structure
- RSI
- ADX
- 1H breakout
- Bullish price action

**Maximum 1H Score = 30**

---

### STEP 4 — 15M Entry Timing

The strongest 1H candidates are then checked for:

- EMA9
- EMA20
- RSI
- Relative volume
- Micro breakout
- Bullish candle
- Entry confirmation

**Maximum 15M Score = 30**

---

# ⭐ Final Quality Score

The final score is normalized to:

## 0–100

It combines:

- Trend
- Momentum
- Breakout
- Volume
- Sector strength
- Price action
- Multi-timeframe confirmation
- Risk/reward

---

# 🏆 Grades

### A+
**88–100**

Exceptional alignment.

### A
**78–87.9**

Strong setup.

### B
**68–77.9**

Good but not elite.

### C
Below 68.

Normally rejected by the strict final filters.

---

# ⚖️ Risk / Reward

V5.1 requires:

## Minimum 1:2 R:R

TP1 = approximately 2R

TP2 = approximately 3R

The stop combines:

- ATR
- Daily structure
- 1H structure
- 15M structure

---

# 🚫 Anti-Chasing Filter

V5.1 rejects stocks that are excessively extended from EMA20.

The objective is to avoid buying after an already-exhausted move.

---

# 🏦 Sector Strength

Stocks are compared with their mapped sector.

Stronger sectors receive a higher quality contribution.

---

# 🛡️ Market Regime

The NIFTY index is classified as:

🟢 BULLISH

🟡 SIDEWAYS

🔴 BEARISH

The stricter the market environment, the stronger the stock requirements become.

---

# ⚡ SPEED OPTIMIZATION

V5.1 uses:

- Cached market data
- Cached individual downloads
- Parallel Daily downloads
- Parallel 1H downloads
- Parallel 15M downloads
- Daily pre-filtering
- 1H pre-filtering
- Intraday scanning only on stronger candidates

This prevents all 500 stocks from receiving expensive 1H + 15M analysis.

---

# 🎯 FINAL OBJECTIVE

The engine is NOT designed to show many stocks.

It is designed to answer:

## "Which stocks currently have the strongest technical alignment?"

The final ranking puts the strongest qualifying setup at the top.

---

## ⚠️ IMPORTANT

This is a technical research and screening system.

A Quality Score is NOT a probability of profit.

Markets can change after the scan.

Always verify:

- Current price
- Liquidity
- Spread
- Corporate events
- News
- Market conditions
- Actual execution price
- Position sizing
- Risk management

before taking any trade.
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

        if not clean.endswith(".NS"):

            clean += ".NS"

        st.divider()

        st.subheader(
            f"🔎 Individual V5.1 Analysis — "
            f"{clean.replace('.NS','')}"
        )

        with st.spinner(
            "Analysing Daily + 1H + 15M..."
        ):

            daily = download_stock(
                clean,
                "2y",
                "1d"
            )

            hourly = download_stock(
                clean,
                "60d",
                "1h"
            )

            m15 = download_stock(
                clean,
                "30d",
                "15m"
            )

            daily_analysis = analyze_daily(
                daily
            )

            hourly_analysis = analyze_hourly(
                hourly
            )

            m15_analysis = analyze_15m(
                m15
            )

            sector_strength = (
                st.session_state.get(
                    "v51_sector_strength",
                    {}
                )
            )

            if not sector_strength:

                sector_strength = {
                    get_sector(clean): 30
                }

            result = analyze_candidate(
                clean,
                daily_analysis,
                hourly_analysis,
                m15_analysis,
                sector_strength,
                regime,
                strict_market
            )

        if result is None:

            st.warning(
                "This stock does not currently pass "
                "the strict V5.1 Best-Setup filters."
            )

        else:

            i1, i2, i3, i4, i5, i6 = st.columns(
                6
            )

            i1.metric(
                "Grade",
                result["Grade"]
            )

            i2.metric(
                "Quality",
                f"{result['Quality']}/100"
            )

            i3.metric(
                "Entry",
                f"₹{result['Entry']}"
            )

            i4.metric(
                "SL",
                f"₹{result['SL']}"
            )

            i5.metric(
                "TP1",
                f"₹{result['TP1']}"
            )

            i6.metric(
                "R:R",
                result["R:R"]
            )

            detail_cols = [
                "Ticker",
                "Sector",
                "Setup",
                "Grade",
                "Quality",
                "Price",
                "Entry",
                "SL",
                "TP1",
                "TP2",
                "R:R",
                "Risk %",
                "Daily",
                "1H",
                "15M",
                "RSI",
                "Vol ×",
                "15M Vol ×",
                "ADX",
                "Candle",
                "20D Breakout",
                "52W Breakout",
                "Market"
            ]

            detail_df = pd.DataFrame(
                [
                    result
                ]
            )

            st.dataframe(
                detail_df[
                    detail_cols
                ],
                use_container_width=True,
                hide_index=True
            )

            st.success(
                f"**Reason:** {result['Reason']}"
            )

            st.subheader(
                "📈 Daily Technical Chart"
            )

            show_chart(
                clean,
                "1y"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Vardha Pro Stock Screener V5.1 • "
    "Optimized Multi-Timeframe Technical Research Engine • "
    "Educational use only"
)
