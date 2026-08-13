# ============================================================
# VARDHA PRO STOCK SCREENER V5.1
# OPTIMIZED BEST-OF-THE-BEST MULTI-TIMEFRAME ENGINE
#
# DAILY  -> NIFTY 500 SELECTION
# 1H     -> SETUP CONFIRMATION
# 15M    -> ENTRY TIMING
#
# OUTPUT:
# TOP 5-15 BEST SETUPS
#
# FEATURES:
# - NIFTY 500 scan
# - Batch daily download
# - Fast candidate filtering
# - 1H confirmation
# - 15M entry confirmation
# - Relative volume
# - Sector strength
# - Market regime
# - Breakout detection
# - Price action
# - Overextension rejection
# - Entry / SL / TP1 / TP2
# - Minimum 1:2 R:R
# - Quality score 0-100
# - A+ / A / B grading
# - Final ranking
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests

from io import StringIO
from datetime import datetime


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

DAILY_PERIOD = "2y"
INTRADAY_1H_PERIOD = "60d"
INTRADAY_15M_PERIOD = "30d"

MIN_DAILY_BARS = 220
MIN_HOURLY_BARS = 50
MIN_15M_BARS = 50

DAILY_BATCH_SIZE = 80

MAX_INTRADAY_CANDIDATES = 90

TOP_MIN = 5
TOP_MAX = 15


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
CANFINHOME CDSL CESC CGPOWER CHAMBLFERT CIPLA COALINDIA COFORGE
COLPAL CONCOR COROMANDEL CROMPTON CUMMINSIND CYIENT DABUR
DALBHARAT DEEPAKNTR DELHIVERY DIVISLAB DIXON DLF DMART
DRREDDY EICHERMOT EIDPARRY EIHOTEL ELGIEQUIP EMAMILTD
ENDURANCE EXIDEIND FEDERALBNK FINCABLE FINEORG FLUOROCHEM
FORTIS GAIL GLAND GLENMARK GODREJCP GODREJPROP GRASIM GRAPHITE
GRINDWELL HAL HAVELLS HCLTECH HDFCAMC HDFCBANK HDFCLIFE
HEROMOTOCO HINDALCO HINDCOPPER HINDPETRO HINDUNILVR HINDZINC
HUDCO ICICIBANK ICICIGI ICICIPRULI IDBI IDFCFIRSTB IEX IGL
INDHOTEL INDIACEM INDIAMART INDIANB INDIGO INDUSINDBK INDUSTOWER
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
TORNTPOWER TRENT TVSMOTOR UBL UCOBANK UJJIVANSFB UNIONBANK UPL
VBL VEDL VGUARD VOLTAS WELCORP WIPRO YESBANK ZEEL ZOMATO
ZYDUSLIFE
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
# LOAD NIFTY 500
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
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
                        s for s in symbols
                        if s
                        and s not in ["NAN", "SYMBOL"]
                    ]
                )
            )

            if len(symbols) >= 450:

                return [
                    s if s.endswith(".NS")
                    else s + ".NS"
                    for s in symbols
                ]

    except Exception:
        pass

    fallback = [
        x.strip().upper()
        for x in FALLBACK_SYMBOLS.split()
        if x.strip()
    ]

    return [
        x if x.endswith(".NS")
        else x + ".NS"
        for x in dict.fromkeys(fallback)
    ]


SYMBOLS = load_universe()


# ============================================================
# CLEAN DATA
# ============================================================

def clean_yf_dataframe(df):

    if df is None or df.empty:
        return None

    try:

        df = df.copy()

        if isinstance(df.columns, pd.MultiIndex):

            # yfinance batch format can be:
            # Price -> Ticker
            # or
            # Ticker -> Price

            level0 = list(df.columns.get_level_values(0))

            required = {
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            }

            if required.issubset(set(level0)):

                df.columns = (
                    df.columns
                    .get_level_values(0)
                )

            else:

                df.columns = (
                    df.columns
                    .get_level_values(-1)
                )

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

        df = df[required].copy()

        for col in required:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        df = df.dropna(
            subset=[
                "Open",
                "High",
                "Low",
                "Close"
            ]
        )

        return df

    except Exception:

        return None


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
            (up > down) &
            (up > 0),
            up,
            0
        ),
        index=df.index
    )

    minus_dm = pd.Series(
        np.where(
            (down > up) &
            (down > 0),
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
        (plus_di - minus_di).abs()
        /
        denominator
    )

    return dx.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()


# ============================================================
# CANDLE
# ============================================================

def candle_pattern(df):

    if df is None or len(df) < 3:
        return "Neutral"

    o = float(df["Open"].iloc[-1])
    h = float(df["High"].iloc[-1])
    l = float(df["Low"].iloc[-1])
    c = float(df["Close"].iloc[-1])

    po = float(df["Open"].iloc[-2])
    pc = float(df["Close"].iloc[-2])

    body = abs(c - o)

    candle_range = max(
        h - l,
        0.00001
    )

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

@st.cache_data(ttl=900, show_spinner=False)
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

        df = clean_yf_dataframe(df)

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

        current = float(
            close.iloc[-1]
        )

        current_rsi = float(
            rsi(close).iloc[-1]
        )

        if (
            current > ema20.iloc[-1]
            and
            ema20.iloc[-1] > ema50.iloc[-1]
            and
            ema50.iloc[-1] > ema200.iloc[-1]
            and
            current_rsi >= 52
        ):
            return "BULLISH"

        if (
            current < ema20.iloc[-1]
            and
            ema20.iloc[-1] < ema50.iloc[-1]
            and
            ema50.iloc[-1] < ema200.iloc[-1]
            and
            current_rsi <= 48
        ):
            return "BEARISH"

        return "SIDEWAYS"

    except Exception:

        return "UNKNOWN"


REGIME = market_regime()


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

    df = clean_yf_dataframe(df)

    if df is None:
        return None

    if len(df) < MIN_DAILY_BARS:
        return None

    close = df["Close"]
    volume = (
        df["Volume"]
        .replace(0, np.nan)
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

    r = rsi(close)
    a = atr(df)
    adx_value = adx(df)

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

    volume_average = volume.rolling(
        20
    ).mean()

    price = float(
        close.iloc[-1]
    )

    previous = float(
        close.iloc[-2]
    )

    current_rsi = float(
        r.iloc[-1]
    )

    current_atr = float(
        a.iloc[-1]
    )

    current_adx = float(
        adx_value.iloc[-1]
    )

    current_volume = float(
        volume.iloc[-1]
    )

    avg_volume = float(
        volume_average.iloc[-1]
    )

    rel_volume = (
        current_volume / avg_volume
        if avg_volume > 0
        else 0
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

    ema20_value = float(
        ema20.iloc[-1]
    )

    ema50_value = float(
        ema50.iloc[-1]
    )

    ema200_value = float(
        ema200.iloc[-1]
    )

    above20 = price > ema20_value
    above50 = price > ema50_value
    above200 = price > ema200_value

    ema_stack = (
        above20
        and above50
        and above200
        and
        ema20_value > ema50_value > ema200_value
    )

    ema_slope = (
        ema20.iloc[-1] >
        ema20.iloc[-6]
    )

    breakout20 = (
        price > resistance20
    )

    near_breakout = (
        price >= resistance20 * 0.985
    )

    breakout52 = (
        price >= high52 * 0.995
    )

    macd_bull = (
        macd.iloc[-1] >
        macd_signal.iloc[-1]
    )

    rsi_good = (
        52 <= current_rsi <= 72
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

    candle = candle_pattern(df)

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

    distance_ema20 = (
        (
            price - ema20_value
        )
        /
        ema20_value
    ) * 100

    overextended = (
        distance_ema20 > 8
    )

    # ========================================================
    # DAILY SCORE /40
    # ========================================================

    score = 0

    # Trend 12
    score += 3 if above20 else 0
    score += 3 if above50 else 0
    score += 3 if above200 else 0
    score += 3 if ema_stack else 0

    # Momentum 8
    score += 3 if rsi_good else 0
    score += 2 if macd_bull else 0
    score += 3 if adx_good else 0

    # Breakout 8
    score += 4 if breakout20 else 0
    score += 2 if near_breakout else 0
    score += 2 if breakout52 else 0

    # Volume 5
    score += 3 if volume_good else 0
    score += 2 if volume_strong else 0

    # Price action 4
    score += 4 if bullish_candle else 0

    # Structure 3
    score += 3 if ema_slope else 0

    if overextended:
        score -= 5

    score = max(
        0,
        min(
            40,
            score
        )
    )

    return {

        "price": price,
        "previous": previous,

        "change_pct": (
            (price / previous - 1) * 100
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

        "bullish_candle": bullish_candle,
        "bearish_candle": bearish_candle,

        "candle": candle,

        "overextended": overextended,
        "distance_ema20": distance_ema20,

        "daily_score": score
    }


# ============================================================
# BATCH DAILY DOWNLOAD
# ============================================================

@st.cache_data(
    ttl=900,
    show_spinner=False
)
def download_daily_batch(
    symbols
):

    result = {}

    if not symbols:
        return result

    try:

        data = yf.download(
            tickers=list(symbols),
            period=DAILY_PERIOD,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="ticker"
        )

        if data is None or data.empty:
            return result

        for symbol in symbols:

            try:

                if isinstance(
                    data.columns,
                    pd.MultiIndex
                ):

                    level0 = (
                        data.columns
                        .get_level_values(0)
                    )

                    level1 = (
                        data.columns
                        .get_level_values(1)
                    )

                    if symbol in level0:

                        stock_df = data[
                            symbol
                        ].copy()

                    elif symbol in level1:

                        stock_df = data[
                            :,
                            pd.IndexSlice[
                                :,
                                symbol
                            ]
                        ].copy()

                        stock_df.columns = (
                            stock_df.columns
                            .get_level_values(0)
                        )

                    else:

                        result[symbol] = None
                        continue

                else:

                    stock_df = data.copy()

                result[symbol] = (
                    clean_yf_dataframe(
                        stock_df
                    )
                )

            except Exception:

                result[symbol] = None

    except Exception:

        for symbol in symbols:
            result[symbol] = None

    return result


# ============================================================
# INTRADAY SINGLE STOCK
# ============================================================

@st.cache_data(
    ttl=600,
    show_spinner=False
)
def download_intraday(
    symbol,
    period,
    interval
):

    try:

        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False
        )

        return clean_yf_dataframe(df)

    except Exception:

        return None


# ============================================================
# HOURLY ANALYSIS
# ============================================================

def analyze_hourly(df):

    df = clean_yf_dataframe(df)

    if df is None:
        return None

    if len(df) < MIN_HOURLY_BARS:
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

    r = rsi(close)
    adx_value = adx(df)

    price = float(
        close.iloc[-1]
    )

    current_rsi = float(
        r.iloc[-1]
    )

    current_adx = float(
        adx_value.iloc[-1]
    )

    ema20_now = float(
        ema20.iloc[-1]
    )

    ema50_now = float(
        ema50.iloc[-1]
    )

    above20 = price > ema20_now
    above50 = price > ema50_now

    stack = (
        above20
        and above50
        and
        ema20_now > ema50_now
    )

    momentum = (
        50 <= current_rsi <= 75
    )

    trend = (
        ema20.iloc[-1] >
        ema20.iloc[-6]
    )

    adx_good = (
        current_adx >= 18
    )

    score = 0

    score += 5 if above20 else 0
    score += 5 if above50 else 0
    score += 5 if stack else 0
    score += 5 if momentum else 0
    score += 5 if trend else 0
    score += 5 if adx_good else 0

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

        "hourly_score": min(
            30,
            score
        )
    }


# ============================================================
# 15 MINUTE ANALYSIS
# ============================================================

def analyze_15m(df):

    df = clean_yf_dataframe(df)

    if df is None:
        return None

    if len(df) < MIN_15M_BARS:
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

    current_rsi = float(
        rsi(close).iloc[-1]
    )

    volume_avg = volume.rolling(
        20
    ).mean()

    current_volume = float(
        volume.iloc[-1]
    )

    avg_volume = float(
        volume_avg.iloc[-1]
    )

    rel_volume = (
        current_volume / avg_volume
        if avg_volume > 0
        else 0
    )

    price = float(
        close.iloc[-1]
    )

    above9 = (
        price >
        float(ema9.iloc[-1])
    )

    above20 = (
        price >
        float(ema20.iloc[-1])
    )

    momentum = (
        50 <= current_rsi <= 75
    )

    volume_expansion = (
        rel_volume >= 1.15
    )

    recent_high = float(
        df["High"]
        .iloc[-11:-1]
        .max()
    )

    micro_breakout = (
        price > recent_high
    )

    candle = candle_pattern(df)

    bullish_candle = candle in [
        "Bullish Engulfing",
        "Hammer",
        "Bullish Candle"
    ]

    entry_confirmation = (
        above9
        and above20
        and
        (
            micro_breakout
            or bullish_candle
        )
    )

    score = 0

    score += 5 if above9 else 0
    score += 5 if above20 else 0
    score += 4 if momentum else 0
    score += 4 if volume_expansion else 0
    score += 5 if micro_breakout else 0
    score += 7 if bullish_candle else 0

    return {

        "price": price,
        "rsi": current_rsi,
        "rel_volume": rel_volume,

        "above9": above9,
        "above20": above20,

        "momentum": momentum,
        "volume_expansion": volume_expansion,

        "micro_breakout": micro_breakout,

        "bullish_candle": bullish_candle,
        "candle": candle,

        "entry_confirmation": entry_confirmation,

        "score": min(
            30,
            score
        ),

        "recent_high": recent_high
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

            sector_scores[sector] = (
                float(
                    np.mean(scores)
                )
            )

        else:

            sector_scores[sector] = 0

    return sector_scores


# ============================================================
# TRADE PLAN
# ============================================================

def create_trade_plan(
    daily,
    hourly,
    m15
):

    if daily is None:
        return None

    price = float(
        daily["price"]
    )

    atr_value = float(
        daily["atr"]
    )

    resistance = float(
        daily["resistance20"]
    )

    support = float(
        daily["support20"]
    )

    if atr_value <= 0:
        return None

    # ========================================================
    # ENTRY
    # ========================================================

    if daily["breakout20"]:

        entry = max(
            price,
            resistance * 1.002
        )

    elif daily["near_breakout"]:

        entry = max(
            price,
            resistance * 1.001
        )

    else:

        entry = price

    # 15M structure
    if m15 is not None:

        micro = float(
            m15["recent_high"]
        )

        if (
            micro > 0
            and micro <= entry * 1.02
        ):

            entry = max(
                entry,
                micro
            )

    # ========================================================
    # STOP LOSS
    # ========================================================

    atr_stop = (
        entry -
        1.5 * atr_value
    )

    structure_stop = (
        support -
        0.20 * atr_value
    )

    # Use the wider protective stop
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
        tp1 - entry
    ) / risk

    rr2 = (
        tp2 - entry
    ) / risk

    if rr1 < 2:
        return None

    return {

        "entry": entry,
        "sl": sl,

        "tp1": tp1,
        "tp2": tp2,

        "rr1": rr1,
        "rr2": rr2,

        "risk": risk
    }


# ============================================================
# GRADE
# ============================================================

def final_grade(score):

    if score >= 85:
        return "A+"

    if score >= 75:
        return "A"

    if score >= 65:
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
    regime
):

    if daily is None:
        return None

    if hourly is None:
        return None

    if m15 is None:
        return None

    # ========================================================
    # HARD MARKET FILTER
    # ========================================================

    if regime == "BEARISH":

        if daily["daily_score"] < 28:
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
                sector_raw / 40
            ) * 10
        )
    )

    daily_score = daily[
        "daily_score"
    ]

    hourly_score = hourly[
        "hourly_score"
    ]

    m15_score = m15[
        "score"
    ]

    # ========================================================
    # HARD CONDITIONS
    # ========================================================

    trend_ok = (
        daily_score >= 25
        and
        hourly_score >= 20
    )

    momentum_ok = (
        daily["rsi"] >= 52
        and
        hourly["rsi"] >= 50
    )

    volume_ok = (
        daily["rel_volume"] >= 1.20
    )

    breakout_ok = (
        daily["breakout20"]
        or
        daily["near_breakout"]
        or
        daily["breakout52"]
        or
        m15["micro_breakout"]
    )

    price_action_ok = (
        daily["bullish_candle"]
        or
        m15["bullish_candle"]
    )

    not_overextended = not (
        daily["overextended"]
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
    # QUALITY SCORE
    # ========================================================

    quality = 0.0

    # --------------------------------------------------------
    # Trend /20
    # --------------------------------------------------------

    quality += (
        daily_score / 40
    ) * 20

    # --------------------------------------------------------
    # Momentum /15
    # --------------------------------------------------------

    momentum_component = 0

    if daily["rsi"] >= 52:
        momentum_component += 5

    if daily["macd_bull"]:
        momentum_component += 5

    if daily["adx"] >= 20:
        momentum_component += 5

    quality += momentum_component

    # --------------------------------------------------------
    # Breakout /15
    # --------------------------------------------------------

    breakout_component = 0

    if daily["breakout20"]:
        breakout_component += 7

    elif daily["near_breakout"]:
        breakout_component += 4

    if daily["breakout52"]:
        breakout_component += 5

    if m15["micro_breakout"]:
        breakout_component += 3

    quality += min(
        15,
        breakout_component
    )

    # --------------------------------------------------------
    # Volume /10
    # --------------------------------------------------------

    quality += min(
        10,
        daily["rel_volume"] * 5
    )

    # --------------------------------------------------------
    # Sector /10
    # --------------------------------------------------------

    quality += sector_score

    # --------------------------------------------------------
    # Price Action /10
    # --------------------------------------------------------

    if (
        daily["bullish_candle"]
        and
        m15["bullish_candle"]
    ):

        quality += 10

    elif (
        daily["bullish_candle"]
        or
        m15["bullish_candle"]
    ):

        quality += 6

    # --------------------------------------------------------
    # MTF /10
    # --------------------------------------------------------

    mtf_component = 0

    if daily_score >= 25:
        mtf_component += 3

    if hourly_score >= 20:
        mtf_component += 3

    if m15_score >= 20:
        mtf_component += 4

    quality += mtf_component

    # --------------------------------------------------------
    # R:R /10
    # --------------------------------------------------------

    quality += min(
        10,
        trade["rr2"] * 3
    )

    # ========================================================
    # PENALTIES
    # ========================================================

    if daily["overextended"]:
        quality -= 12

    if regime == "BEARISH":
        quality -= 8

    elif regime == "SIDEWAYS":
        quality -= 3

    if not volume_ok:
        quality -= 5

    if not breakout_ok:
        quality -= 4

    if not price_action_ok:
        quality -= 3

    quality = max(
        0,
        min(
            100,
            quality
        )
    )

    # ========================================================
    # STRICT FILTERS
    # ========================================================

    if quality < 65:
        return None

    if not trend_ok:
        return None

    if not momentum_ok:
        return None

    if not volume_ok:
        return None

    if not not_overextended:
        return None

    if trade["rr1"] < 2:
        return None

    if (
        not m15["entry_confirmation"]
        and
        m15_score < 18
    ):
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
        m15["micro_breakout"]
    ):

        setup_type = (
            "Confirmed Breakout"
        )

    elif (
        daily["near_breakout"]
        and
        daily["bullish_candle"]
    ):

        setup_type = (
            "Breakout Continuation"
        )

    elif (
        daily["ema20"] >
        daily["ema50"]
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

    if daily["ema20"] > daily["ema50"]:
        reasons.append(
            "EMA20 > EMA50"
        )

    if daily["ema50"] > daily["ema200"]:
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

    if daily["rel_volume"] >= 1.5:
        reasons.append(
            "Strong volume"
        )

    elif daily["rel_volume"] >= 1.2:
        reasons.append(
            "Volume expansion"
        )

    if daily["bullish_candle"]:
        reasons.append(
            daily["candle"]
        )

    if hourly["stack"]:
        reasons.append(
            "1H trend confirmation"
        )

    if m15["micro_breakout"]:
        reasons.append(
            "15M breakout"
        )

    if m15["bullish_candle"]:
        reasons.append(
            "15M bullish price action"
        )

    reason_text = " • ".join(
        reasons[:8]
    )

    # ========================================================
    # RESULT
    # ========================================================

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
# CHART
# ============================================================

def show_chart(
    symbol,
    period="1y"
):

    df = download_intraday(
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

st.title(
    "🔥 Vardha Pro Stock Screener V5.1"
)

st.caption(
    "Optimized Best-of-the-Best Multi-Timeframe Setup Engine"
)

st.caption(
    f"NIFTY Universe: {len(SYMBOLS)} symbols • "
    f"Market Regime: {REGIME}"
)

st.warning(
    "Educational/research tool only. "
    "Technical scores are rule-based quality measures "
    "and do not guarantee profit."
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
            s
            for s in scan_symbols
            if s.replace(
                ".NS",
                ""
            ).upper()
            in allowed
        ]

    st.header(
        "🛡️ Market Filters"
    )

    strict_market = st.checkbox(
        "Strict market regime",
        True
    )

    st.header(
        "⚡ Speed"
    )

    max_intraday = st.slider(
        "Maximum intraday candidates",
        30,
        120,
        MAX_INTRADAY_CANDIDATES,
        10
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
        0
    )

    status = st.empty()

    # ========================================================
    # PASS 1
    # BATCH DAILY
    # ========================================================

    daily_cache = {}

    total = len(
        scan_symbols
    )

    if total == 0:

        st.error(
            "No symbols available."
        )

        st.stop()

    status.write(
        f"📅 Downloading daily data for "
        f"{total} stocks in optimized batches..."
    )

    batches = [
        scan_symbols[i:i + DAILY_BATCH_SIZE]
        for i in range(
            0,
            total,
            DAILY_BATCH_SIZE
        )
    ]

    for batch_index, batch in enumerate(
        batches
    ):

        batch_data = (
            download_daily_batch(
                tuple(batch)
            )
        )

        for symbol in batch:

            daily = analyze_daily(
                batch_data.get(symbol)
            )

            daily_cache[
                symbol
            ] = daily

        progress.progress(
            (
                (batch_index + 1)
                /
                max(
                    len(batches),
                    1
                )
            ) * 0.45
        )

    # ========================================================
    # SECTOR STRENGTH
    # ========================================================

    status.write(
        "🏦 Calculating sector strength..."
    )

    sector_strength = (
        calculate_sector_strength(
            daily_cache
        )
    )

    # ========================================================
    # DAILY PRE-FILTER
    # ========================================================

    status.write(
        "🔎 Filtering strongest daily setups..."
    )

    candidates = []

    for symbol, daily in daily_cache.items():

        if daily is None:
            continue

        # Market filter
        if (
            strict_market
            and
            REGIME == "BEARISH"
        ):

            if daily["daily_score"] < 28:
                continue

        else:

            if daily["daily_score"] < 23:
                continue

        # Reject extreme extension
        if daily["overextended"]:
            continue

        # Minimum volume
        if daily["rel_volume"] < 1.10:
            continue

        # Need at least one meaningful structure
        structure_ok = (
            daily["breakout20"]
            or
            daily["near_breakout"]
            or
            daily["breakout52"]
            or
            daily["ema20"] > daily["ema50"]
        )

        if not structure_ok:
            continue

        candidates.append(
            symbol
        )

    # ========================================================
    # DAILY RANKING
    # ========================================================

    candidates = sorted(
        candidates,
        key=lambda x: (
            daily_cache[x]["daily_score"],
            daily_cache[x]["rel_volume"],
            daily_cache[x]["adx"],
            daily_cache[x]["rsi"]
        ),
        reverse=True
    )

    # Only strongest candidates receive
    # expensive intraday requests
    candidates = candidates[
        :min(
            max_intraday,
            len(candidates)
        )
    ]

    st.session_state[
        "v51_daily_candidates"
    ] = len(candidates)

    # ========================================================
    # PASS 2
    # 1H + 15M
    # ========================================================

    hourly_cache = {}
    m15_cache = {}

    candidate_total = len(
        candidates
    )

    if candidate_total == 0:

        status.empty()
        progress.empty()

        st.session_state[
            "v51_results"
        ] = pd.DataFrame()

        st.session_state[
            "v51_scanned"
        ] = total

        st.session_state[
            "v51_scan_time"
        ] = round(
            (
                datetime.now()
                -
                start_time
            ).total_seconds(),
            1
        )

        st.session_state[
            "v51_sector_strength"
        ] = sector_strength

    else:

        for i, symbol in enumerate(
            candidates
        ):

            clean_symbol = (
                symbol.replace(
                    ".NS",
                    ""
                )
            )

            status.write(
                f"⏱️ MTF analysis: "
                f"{clean_symbol} "
                f"({i+1}/{candidate_total})"
            )

            # ------------------------------------------------
            # 1H
            # ------------------------------------------------

            hourly_df = download_intraday(
                symbol,
                INTRADAY_1H_PERIOD,
                "1h"
            )

            hourly = analyze_hourly(
                hourly_df
            )

            hourly_cache[
                symbol
            ] = hourly

            # ------------------------------------------------
            # 15M
            # ------------------------------------------------

            m15_df = download_intraday(
                symbol,
                INTRADAY_15M_PERIOD,
                "15m"
            )

            m15 = analyze_15m(
                m15_df
            )

            m15_cache[
                symbol
            ] = m15

            progress.progress(
                0.45 +
                (
                    (
                        (i + 1)
                        /
                        max(
                            candidate_total,
                            1
                        )
                    )
                    *
                    0.55
                )
            )

        # ====================================================
        # FINAL RANKING
        # ====================================================

        status.write(
            "🏆 Calculating final quality ranking..."
        )

        final_results = []

        for symbol in candidates:

            result = analyze_candidate(
                symbol,
                daily_cache.get(symbol),
                hourly_cache.get(symbol),
                m15_cache.get(symbol),
                sector_strength,
                REGIME
            )

            if result is not None:

                final_results.append(
                    result
                )

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

            result_df[
                "GradeOrder"
            ] = (
                result_df[
                    "Grade"
                ]
                .map(
                    grade_order
                )
                .fillna(9)
            )

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

        # ====================================================
        # SESSION
        # ====================================================

        st.session_state[
            "v51_results"
        ] = result_df

        st.session_state[
            "v51_scanned"
        ] = total

        st.session_state[
            "v51_candidates"
        ] = candidate_total

        st.session_state[
            "v51_scan_time"
        ] = round(
            (
                datetime.now()
                -
                start_time
            ).total_seconds(),
            1
        )

        st.session_state[
            "v51_sector_strength"
        ] = sector_strength

    progress.empty()
    status.empty()


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

    candidates_count = (
        st.session_state.get(
            "v51_candidates",
            0
        )
    )

    scan_time = (
        st.session_state.get(
            "v51_scan_time",
            0
        )
    )

    # ========================================================
    # RESULTS HEADER
    # ========================================================

    st.subheader(
        "🏆 BEST-OF-THE-BEST V5.1 SETUPS"
    )

    if df is None or df.empty:

        st.error(
            "No setup passed all strict V5.1 filters."
        )

        st.write(
            "The engine scanned the universe but "
            "no stock currently satisfies the complete "
            "Daily + 1H + 15M + Volume + R:R criteria."
        )

    else:

        aplus = int(
            (
                df["Grade"] == "A+"
            ).sum()
        )

        agrade = int(
            (
                df["Grade"] == "A"
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
            "🎯 Daily Candidates",
            candidates_count
        )

        c3.metric(
            "🔥 A+",
            aplus
        )

        c4.metric(
            "⭐ Best Quality",
            f"{best_quality}/100"
        )

        c5.metric(
            "📊 Avg Quality",
            f"{avg_quality}/100"
        )

        c6.metric(
            "⚡ Scan Time",
            f"{scan_time}s"
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

                    x1, x2, x3, x4 = st.columns(
                        4
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

                    st.write(
                        f"**Setup:** {row['Setup']}"
                    )

                    st.write(
                        f"**Sector:** {row['Sector']}"
                    )

                    st.write(
                        f"**R:R:** {row['R:R']}"
                    )

                    st.write(
                        f"**Daily:** {row['Daily']}/40 | "
                        f"**1H:** {row['1H']}/30 | "
                        f"**15M:** {row['15M']}/30"
                    )

                    st.write(
                        f"**RSI:** {row['RSI']} | "
                        f"**Volume:** {row['Vol ×']}× | "
                        f"**ADX:** {row['ADX']}"
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
                "Daily",
                "1H",
                "15M",
                "RSI",
                "Vol ×",
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
                "R:R"
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
                "Entry, SL and targets are "
                "rule-based research levels and "
                "are not guaranteed execution prices."
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

## ⚡ Optimized Architecture

### PASS 1 — NIFTY 500 Daily

The engine first scans the complete NIFTY universe.

Daily checks:

- EMA20
- EMA50
- EMA200
- EMA stacking
- EMA slope
- RSI
- MACD
- ADX
- 20D breakout
- 52W strength
- Relative volume
- Candlestick structure
- Overextension

Maximum Daily score:

**40 points**

---

## PASS 2 — Candidate Selection

Weak stocks are removed before intraday analysis.

The engine rejects:

- Weak trend
- Low volume
- Excessive extension
- Poor structure
- Weak market conditions

Only the strongest candidates continue to the expensive intraday analysis.

---

## PASS 3 — 1H Confirmation

Checks:

- EMA20
- EMA50
- EMA stacking
- RSI
- Trend slope
- ADX
- Momentum

Maximum:

**30 points**

---

## PASS 4 — 15M Entry Timing

Checks:

- EMA9
- EMA20
- RSI
- Relative volume
- Micro breakout
- Bullish candle
- Entry confirmation

Maximum:

**30 points**

---

# ⭐ FINAL QUALITY SCORE

The final score combines:

- Trend
- Momentum
- Breakout
- Volume
- Sector strength
- Price action
- Multi-timeframe confirmation
- Risk/reward

Final:

**0–100**

---

# 🏆 GRADES

### A+

**85–100**

Highest-quality setups.

### A

**75–84.9**

Strong setups.

### B

**65–74.9**

Acceptable but lower quality.

Anything below 65 is rejected.

---

# ⚖️ RISK / REWARD

V5.1 requires:

**Minimum 1:2 R:R**

Targets:

- TP1 = 2R
- TP2 = 3R

Stop uses:

- ATR
- 20-day structure

---

# 🚫 OVEREXTENSION FILTER

The system attempts to avoid chasing stocks that are excessively far above EMA20.

This helps reduce:

**Late-entry / FOMO setups**

---

# 🏦 SECTOR STRENGTH

Stocks receive additional quality points based on their sector's average Daily strength.

Strong sectors can therefore receive a higher ranking.

---

# 🛡️ MARKET REGIME

The NIFTY market is classified as:

🟢 BULLISH

🟡 SIDEWAYS

🔴 BEARISH

In bearish conditions the screening becomes stricter.

---

# ⚠️ IMPORTANT

This is a technical research and screening engine.

A Quality Score is NOT a probability of profit.

Entry/SL/TP are rule-based research levels.

Always verify:

- Current price
- Liquidity
- Spread
- News
- Corporate events
- Market conditions
- Execution conditions
- Your own risk management

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

        daily_df = download_intraday(
            clean,
            DAILY_PERIOD,
            "1d"
        )

        hourly_df = download_intraday(
            clean,
            INTRADAY_1H_PERIOD,
            "1h"
        )

        m15_df = download_intraday(
            clean,
            INTRADAY_15M_PERIOD,
            "15m"
        )

        daily_analysis = analyze_daily(
            daily_df
        )

        hourly_analysis = analyze_hourly(
            hourly_df
        )

        m15_analysis = analyze_15m(
            m15_df
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
            REGIME
        )

        if result is None:

            st.warning(
                "This stock does not currently "
                "pass the strict V5.1 Best-Setup filters."
            )

            # Show raw daily analysis
            if daily_analysis:

                st.write(
                    "### Daily Snapshot"
                )

                d1, d2, d3, d4, d5 = st.columns(
                    5
                )

                d1.metric(
                    "Daily Score",
                    f"{daily_analysis['daily_score']}/40"
                )

                d2.metric(
                    "RSI",
                    round(
                        daily_analysis["rsi"],
                        1
                    )
                )

                d3.metric(
                    "Volume",
                    f"{daily_analysis['rel_volume']:.2f}x"
                )

                d4.metric(
                    "ADX",
                    round(
                        daily_analysis["adx"],
                        1
                    )
                )

                d5.metric(
                    "Candle",
                    daily_analysis["candle"]
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
                "Daily",
                "1H",
                "15M",
                "RSI",
                "Vol ×",
                "ADX",
                "Candle",
                "20D Breakout",
                "52W Breakout",
                "Market"
            ]

            detail_df = pd.DataFrame(
                [result]
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
