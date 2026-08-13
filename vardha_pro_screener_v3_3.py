import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from io import StringIO

st.set_page_config(
    page_title="Vardha Pro Stock Screener V4",
    page_icon="📈",
    layout="wide"
)

# ============================================================
# NIFTY 500 UNIVERSE
# ============================================================

@st.cache_data(ttl=86400)
def load_nifty500():

    urls = [
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
        "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    ]

    for url in urls:

        try:
            r = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            if r.status_code == 200:

                df = pd.read_csv(
                    StringIO(r.text)
                )

                if "Symbol" in df.columns:

                    symbols = (
                        df["Symbol"]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                        .dropna()
                        .tolist()
                    )

                    symbols = list(
                        dict.fromkeys(symbols)
                    )

                    if len(symbols) >= 450:

                        return [
                            s + ".NS"
                            for s in symbols
                        ]

        except Exception:
            continue

    # --------------------------------------------------------
    # Fallback: broad NSE universe
    # --------------------------------------------------------

    fallback = """
    RELIANCE TCS HDFCBANK ICICIBANK INFY HINDUNILVR ITC SBIN
    BHARTIARTL KOTAKBANK LT AXISBANK HCLTECH MARUTI SUNPHARMA
    M&M TATAMOTORS TITAN ULTRACEMCO ASIANPAINT NTPC POWERGRID
    ONGC COALINDIA BAJFINANCE BAJAJFINSV TATASTEEL JSWSTEEL
    WIPRO TECHM ADANIENT ADANIPORTS BEL HAL TRENT ZOMATO DLF
    DIVISLAB DRREDDY CIPLA APOLLOHOSP LUPIN BIOCON GLENMARK
    TORNTPHARM MAXHEALTH FORTIS EICHERMOT HEROMOTOCO TVSMOTOR
    BAJAJ-AUTO BOSCHLTD HINDALCO VEDL JINDALSTEL SAIL NMDC
    NATIONALUM BPCL IOC GAIL OIL PFC REC NHPC TATAPOWER
    ADANIGREEN ADANIPOWER SIEMENS ABB BHEL CGPOWER CUMMINSIND
    KEI POLYCAB DIXON LTIM MPHASIS PERSISTENT OFSS COFORGE
    FEDERALBNK CANBK BANKBARODA IDFCFIRSTB AUBANK BANDHANBNK
    BANKINDIA IDBI LICHSGFIN MUTHOOTFIN MANAPPURAM SHRIRAMFIN
    SBICARD ICICIPRULI ICICIGI BRITANNIA DABUR MARICO GODREJCP
    COLPAL TATACONSUM VBL GODREJPROP OBEROIRLTY PHOENIXLTD
    PRESTIGE LODHA BRIGADE HAVELLS CROMPTON VOLTAS KALYANKJIL
    PAGEIND DMART WHIRLPOOL

    3MINDIA AARTIIND AAVAS AEGISCHEM AFFLE AMBER APLAPOLLO
    APARINDS ASTRAL ATUL AUROPHARMA BALKRISIND BATAINDIA
    BAYERCROP BLUESTARCO CANFINHOME CASTROLIND CEATLTD
    CENTRALBK CENTURYPLY CESC CHAMBLFERT CHOLAFIN COCHINSHIP
    COROMANDEL CYIENT DATAPATTNS DELHIVERY DEVYANI EIDPARRY
    EMAMILTD ENDURANCE ENGRO ENGINEERSIN EQUITASBNK EXIDEIND
    FINCABLE FINPIPE FLUOROCHEM GESHIP GICRE GLAND GRANULES
    GRAPHITE GREENPANEL GRINDWELL GSPL GUJGASLTD HAPPSTMNDS
    HATSUN HDFCAMC HINDCOPPER HINDPETRO HINDZINC HOMEFIRST
    HUDCO IEX IGL INDHOTEL INDIACEM INDIAMART INDIANB INDIGO
    INDIANHUME INOXWIND IRCTC IRFC IREDA ISEC ITDC JAMNAAUTO
    JINDALSAW JK CEMENT JKCEMENT JSL JUBLFOOD KAYNES KPIL
    LAURUSLABS LAXMIMACHINE LEMONTREE MGL MINDACORP MOTHERSON
    MOTILALOFS NATIONALUM NAVINFLUOR NBCC NLCINDIA NOCIL
    OFSS OLECTRA OMAXE ORIENTELEC PAGEIND PCBL PEL PETRONET
    PFIZER PNB POLYCAB PRAJIND PVRINOX RAINBOW RBLBANK
    REDINGTON ROUTE SAPPHIRE SCHAEFFLER SHREECEM SKFIND
    SONACOMS SONATSOFTW STARHEALTH SUMICHEM SUPREMEIND
    SUNDARMFIN SUNTECK SUPRAJIT SYMPHONY TATACHEM TATACOMM
    TATATECH TRIDENT TRIVENI UCOBANK UJJIVANSFB UNIONBANK
    UPL UTIAMC VAKRANGEE VARROC VEDANT VESUVIUS VIJAYA
    WELSPUN WESTLIFE WOCKPHARMA YESBANK ZEEL ZENSARTECH
    ZYDUSLIFE ABCAPITAL ABFRL ACC ALKEM ALKYLAMINE ASHOKLEY
    ASTRAL BDL BEML BIKAJI BIRLACORPN BRIGADE CARBORUNIV
    CERA CHEMPLAST CIEINDIA CRAFTSMAN CREDITACC DCMSHRIRAM
    DEEPAKNTR ECLERX EIHOTEL ELGIEQUIP ERIS FDC FINEORG
    FIVESTAR GABRIEL GARFIBRES GILLETTE GLAXO HCG HINDWARE
    HONASA HONAUT ICRA IIFL IIFLWAM INDIACEM INDIGOPNTS
    INOXGREEN IRB IRCON JBCHEPHARM JKLAKSHMI JKPAPER
    JUBLINGREA KANSAINER KEC KFINTECH KNRCON KRBL LALPATHLAB
    LATENTVIEW LICI MAHABANK MAHSEAMLES MAHLOG MARATHON
    MCX MEDANTA MEDPLUS METROPOLIS MIDHANI MIRZAINT MRPL
    MSTCLTD NATCOPHARM NAZARA NBCC NBIFIN NEOGEN NESCO
    NETWORK18 NEWGEN NIITLTD NITINSPIN OBEROIRLTY OIL OLAELEC
    ORIENTCEM PNCINFRA POONAWALLA PPLPHARMA PRAJIND PRICOLLTD
    PRINCEPIPE RAILTEL RITES ROSSARI RPOWER RVNL SAKSOFT
    SAMHI SANDHAR SANGHVIMOV SARDAEN SAREGAMA SCHNEIDER
    SEQUENT SHARDACROP SHILPAMED SHRIRAMFIN SOBHA STLTECH
    TANLA TCI TCIEXP TEGAS THERMAX THOMASCOOK TITAGARH TMB
    TURBO UCOBANK UJJIVANSFB UNIONBANK UPL UTIAMC VARROC
    VIJAYA WELSPUN YESBANK
    """

    symbols = fallback.split()

    symbols = list(
        dict.fromkeys(symbols)
    )

    return [
        s + ".NS"
        for s in symbols
    ]


SYMBOLS = load_nifty500()


# ============================================================
# INDICATORS
# ============================================================

def calc_rsi(close, n=14):

    delta = close.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.ewm(
        alpha=1 / n,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / n,
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


def calc_atr(df, n=14):

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


def calculate_stock(
    ticker,
    data
):

    try:

        if data is None or data.empty:
            return None

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            data.columns = (
                data.columns
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
            x in data.columns
            for x in required
        ):
            return None

        df = data.dropna(
            subset=required
        ).copy()

        if len(df) < 60:
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

        ema200 = close.ewm(
            span=200,
            adjust=False
        ).mean()

        rsi = calc_rsi(
            close
        )

        atr = calc_atr(
            df
        )

        volume = (
            df["Volume"]
            .replace(
                0,
                np.nan
            )
        )

        volume_avg = (
            volume
            .rolling(20)
            .mean()
        )

        volx = (
            volume.iloc[-1] /
            volume_avg.iloc[-1]
        )

        resistance = float(
            df["High"]
            .iloc[-21:-1]
            .max()
        )

        support = float(
            df["Low"]
            .iloc[-21:-1]
            .min()
        )

        price = float(
            close.iloc[-1]
        )

        atr_value = float(
            atr.iloc[-1]
        )

        breakout = (
            price > resistance
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

        rsi_value = float(
            rsi.iloc[-1]
        )

        momentum = (
            55 <= rsi_value <= 75
        )

        volume_good = (
            volx >= 1.2
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

        macd_signal = (
            macd.ewm(
                span=9,
                adjust=False
            ).mean()
        )

        macd_bull = (
            macd.iloc[-1] >
            macd_signal.iloc[-1]
        )

        ema_stack = (
            above20
            and above50
            and above200
            and ema20.iloc[-1]
            > ema50.iloc[-1]
        )

        score = sum(
            [
                above20,
                above50,
                above200,
                momentum,
                volume_good,
                breakout,
                macd_bull,
                ema_stack
            ]
        )

        if (
            score >= 7
            and breakout
            and volume_good
        ):
            signal = "STRONG BUY"

        elif (
            score >= 6
            and (
                breakout
                or price >= resistance * 0.985
            )
            and volume_good
        ):
            signal = "BUY"

        elif score >= 4:
            signal = "WATCH"

        else:
            signal = "AVOID"

        entry = (
            max(
                price,
                resistance * 1.002
            )
            if price >= resistance * 0.985
            else price
        )

        sl = min(
            support,
            entry - 1.5 * atr_value
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

        return {

            "Ticker":
                ticker.replace(
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
                    rsi_value,
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

            "Support":
                round(
                    support,
                    2
                ),

            "Resistance":
                round(
                    resistance,
                    2
                ),

            "Breakout":
                "YES"
                if breakout
                else "NO",

            "MACD":
                "BULLISH"
                if macd_bull
                else "BEARISH",

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

            "Score":
                f"{score}/8",

            "ScoreNum":
                score,

            "Signal":
                signal
        }

    except Exception:
        return None


# ============================================================
# SECTORS
# ============================================================

SECTORS = {

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
        "SHRIRAMFIN",
        "BAJFINANCE",
        "BAJAJFINSV",
        "SBICARD"
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
        "BAJAJ-AUTO",
        "BOSCHLTD"
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
        "DIXON",
        "THERMAX"
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
        "PAGEIND",
        "WHIRLPOOL"
    }
}


def sector_filter(
    symbols,
    sector
):

    if sector == "All sectors":
        return symbols

    allowed = SECTORS.get(
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

st.title(
    "📈 Vardha Pro Stock Screener V4"
)

st.caption(
    f"Universe loaded: {len(SYMBOLS)} symbols"
)

st.caption(
    "NIFTY 500 • Batch scanning • "
    "Momentum • Trend • Breakout • Volume • "
    "Price Action"
)

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
            "Enter symbols",
            "RELIANCE, TCS, INFY"
        )

        custom = [
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
            for x in custom
        ]

    else:

        symbols = SYMBOLS.copy()

    st.header(
        "Filters"
    )

    period = st.selectbox(
        "History",
        [
            "6mo",
            "1y",
            "2y"
        ]
    )

    min_score = st.slider(
        "Minimum score",
        3,
        8,
        4
    )

    sector = st.selectbox(
        "Sector",
        [
            "All sectors"
        ]
        +
        list(
            SECTORS.keys()
        )
    )

    scan = st.button(
        "🔎 SCAN NOW",
        type="primary",
        use_container_width=True
    )


# ============================================================
# SCAN
# ============================================================

if scan:

    symbols = sector_filter(
        symbols,
        sector
    )

    st.info(
        f"Scanning {len(symbols)} stocks..."
    )

    progress = st.progress(0)

    try:

        data = yf.download(
            symbols,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True
        )

    except Exception as e:

        st.error(
            f"Yahoo Finance download error: {e}"
        )

        data = None

    rows = []

    if data is not None and not data.empty:

        total = len(symbols)

        for i, ticker in enumerate(symbols):

            try:

                if isinstance(
                    data.columns,
                    pd.MultiIndex
                ):

                    if ticker not in data.columns.get_level_values(0):

                        progress.progress(
                            (i + 1) / total
                        )

                        continue

                    stock_df = data[
                        ticker
                    ].copy()

                else:

                    stock_df = data.copy()

                result = calculate_stock(
                    ticker,
                    stock_df
                )

                if result:
                    rows.append(result)

            except Exception:
                pass

            progress.progress(
                (i + 1) / total
            )

    progress.empty()

    if rows:

        results = pd.DataFrame(
            rows
        )

        results = results.sort_values(
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
        )

        st.success(
            f"Scan completed: "
            f"{len(results)} stocks successfully analysed."
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Stocks scanned",
            len(results)
        )

        c2.metric(
            "BUY",
            int(
                results[
                    "Signal"
                ].isin(
                    [
                        "BUY",
                        "STRONG BUY"
                    ]
                ).sum()
            )
        )

        c3.metric(
            "WATCH",
            int(
                (
                    results[
                        "Signal"
                    ] == "WATCH"
                ).sum()
            )
        )

        c4.metric(
            "Best score",
            f"{int(results.ScoreNum.max())}/8"
        )

        st.subheader(
            "🔥 Top Setups"
        )

        top = results[
            results["ScoreNum"]
            >= min_score
        ].head(15)

        if top.empty:

            st.warning(
                "No stocks matched "
                "the selected score."
            )

        else:

            st.dataframe(
                top[
                    [
                        "Ticker",
                        "Price",
                        "RSI",
                        "Vol ×",
                        "EMA20",
                        "EMA50",
                        "EMA200",
                        "Breakout",
                        "Score",
                        "Signal"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        tab1, tab2 = st.tabs(
            [
                "📊 All Results",
                "🎯 Trade Plans"
            ]
        )

        with tab1:

            st.dataframe(
                results[
                    [
                        "Ticker",
                        "Price",
                        "Change %",
                        "RSI",
                        "Vol ×",
                        "EMA20",
                        "EMA50",
                        "EMA200",
                        "Support",
                        "Resistance",
                        "Breakout",
                        "MACD",
                        "Score",
                        "Signal"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Download CSV",
                results.drop(
                    columns=[
                        "ScoreNum"
                    ]
                ).to_csv(
                    index=False
                ).encode(
                    "utf-8"
                ),
                "vardha_pro_screener.csv",
                "text/csv"
            )

        with tab2:

            plans = results[
                results["Signal"].isin(
                    [
                        "BUY",
                        "STRONG BUY",
                        "WATCH"
                    ]
                )
            ].head(20)

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
                        "Score"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Entry, SL and TP are "
                "rule-based research levels "
                "and are not personalized "
                "investment advice."
            )

    else:

        st.error(
            "No stocks could be analysed. "
            "Please try again."
        )

else:

    st.info(
        "Select your filters and click "
        "🔎 SCAN NOW."
    )
