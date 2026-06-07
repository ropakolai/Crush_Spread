import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Soybean Crush Spread",
    page_icon="🌱",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif;
        background-color: #0d1117;
        color: #e6edf3;
    }

    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #0f1e2e 50%, #0d1117 100%);
    }

    h1 {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 2.6rem;
        background: linear-gradient(90deg, #f5c518, #f0a500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
        margin-bottom: 0;
    }

    h2, h3 {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
    }

    .subtitle {
        font-family: 'Space Mono', monospace;
        color: #7d8590;
        font-size: 0.85rem;
        letter-spacing: 2px;
        margin-top: 4px;
        text-transform: uppercase;
    }

    .metric-card {
        background: linear-gradient(145deg, #161b22, #1c2330);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #f5c518;
    }

    .metric-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 2px;
        color: #7d8590;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .metric-ticker {
        font-family: 'Space Mono', monospace;
        font-size: 0.78rem;
        color: #f5c518;
        margin-bottom: 8px;
    }

    .metric-value {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #e6edf3;
        line-height: 1;
    }

    .metric-unit {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #7d8590;
        margin-top: 4px;
    }

    .crush-card {
        background: linear-gradient(145deg, #1a2332, #0f2040);
        border: 2px solid #f5c518;
        border-radius: 16px;
        padding: 28px 36px;
        text-align: center;
        box-shadow: 0 0 40px rgba(245, 197, 24, 0.15);
    }

    .crush-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 3px;
        color: #f5c518;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .crush-value {
        font-family: 'Syne', sans-serif;
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1;
    }

    .crush-formula {
        font-family: 'Space Mono', monospace;
        font-size: 0.72rem;
        color: #7d8590;
        margin-top: 10px;
    }

    .positive { color: #3fb950; }
    .negative { color: #f85149; }
    .neutral  { color: #e6edf3; }

    .delta-badge {
        display: inline-block;
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        margin-top: 6px;
    }
    .delta-pos { background: rgba(63,185,80,0.12); color: #3fb950; }
    .delta-neg { background: rgba(248,81,73,0.12); color: #f85149; }

    .info-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #f5c518;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 0.85rem;
        color: #8b949e;
        font-family: 'Space Mono', monospace;
    }

    .stButton > button {
        background: linear-gradient(135deg, #f5c518, #f0a500);
        color: #0d1117;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        border: none;
        border-radius: 8px;
        padding: 10px 28px;
        letter-spacing: 0.5px;
        cursor: pointer;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }

    .stSelectbox label, .stSlider label {
        font-family: 'Space Mono', monospace;
        font-size: 0.78rem;
        letter-spacing: 1px;
        color: #7d8590;
        text-transform: uppercase;
    }

    div[data-testid="stMetricValue"] {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
    }

    .timestamp {
        font-family: 'Space Mono', monospace;
        font-size: 0.68rem;
        color: #484f58;
        text-align: right;
        margin-top: 2px;
    }

    hr { border-color: #21262d; }

    .section-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 3px;
        color: #484f58;
        text-transform: uppercase;
        margin-bottom: 12px;
        margin-top: 24px;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
CONTRACTS = {
    "ZS=F": {"name": "Soja",          "unit": "$/boisseau",    "multiplier": 0.01},
    "ZL=F": {"name": "Huile de Soja", "unit": "$/lb",          "multiplier": 0.01},
    "ZM=F": {"name": "Tourteau",      "unit": "$/tonne courte","multiplier": 1},
}

@st.cache_data(ttl=60)
def fetch_prices(period: str = "6mo"):
    """Fetch current prices and historical data, ticker by ticker for robustness."""
    tickers = list(CONTRACTS.keys())
    current = {}
    prev    = {}
    hist_frames = {}

    for t in tickers:
        try:
            df = yf.Ticker(t).history(period=period, auto_adjust=True)
            closes = df["Close"].dropna()
            if len(closes) == 0:
                raise ValueError("empty")
            current[t] = float(closes.iloc[-1])
            prev[t]    = float(closes.iloc[-2]) if len(closes) > 1 else float(closes.iloc[-1])
            hist_frames[t] = closes
        except Exception:
            current[t] = None
            prev[t]    = None
            hist_frames[t] = pd.Series(dtype=float)

    # Combine into a single DataFrame aligned on dates
    hist = pd.DataFrame(hist_frames)
    hist.columns = [c.replace("=F", "") for c in hist.columns]

    return current, prev, hist


def crush_spread(zs, zl, zm):
    """11 * (ZL/100)  +  0.022 * ZM  –  (ZS/100)  (résultat en $/boisseau)
    ZS et ZL sont cotés en ¢ → divisés par 100"""
    if None in (zs, zl, zm):
        return None
    return 11 * (zl / 100) + 0.022 * zm - (zs / 100)


def color_class(val):
    if val is None: return "neutral"
    return "positive" if val >= 0 else "negative"


def fmt(val, decimals=2):
    if val is None: return "N/A"
    return f"{val:,.{decimals}f}"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<h1>🌱 Soybean Crush Spread</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">CBOT · ZS · ZL · ZM · Temps réel</p>', unsafe_allow_html=True)
st.markdown("---")

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")
    period = st.selectbox(
        "Historique",
        options=["1mo", "3mo", "6mo", "1y", "2y"],
        index=2,
        format_func=lambda x: {
            "1mo": "1 mois", "3mo": "3 mois", "6mo": "6 mois",
            "1y": "1 an", "2y": "2 ans"
        }[x]
    )
    auto_refresh = st.checkbox("Actualisation auto (60s)", value=False)
    st.markdown("---")
    st.markdown('<div class="info-box">Formule :<br><br>11 × ZL (¢/lb)<br>+ 0.022 × ZM ($/tc)<br>– 0.01 × ZS (¢/bss)<br><br>Résultat en $/boisseau.</div>', unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Chargement des données CBOT…"):
    current, prev, hist = fetch_prices(period)

now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ── Current prices row ────────────────────────────────────────────────────────
st.markdown('<p class="section-title">Prix des contrats actifs</p>', unsafe_allow_html=True)

cols = st.columns(3)
tickers_ordered = ["ZS=F", "ZL=F", "ZM=F"]

for i, ticker in enumerate(tickers_ordered):
    info  = CONTRACTS[ticker]
    mult  = info["multiplier"]
    price = current[ticker]
    p     = prev[ticker]
    price_d = price * mult if price else None
    p_d     = p * mult if p else None
    delta = (price_d - p_d) if (price_d and p_d) else None
    pct   = (delta / p_d * 100) if (delta and p_d) else None

    delta_html = ""
    if delta is not None:
        sign  = "+" if delta >= 0 else ""
        cls   = "delta-pos" if delta >= 0 else "delta-neg"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<span class="delta-badge {cls}">{arrow} {sign}{fmt(delta, 4)} ({sign}{fmt(pct, 2)}%)</span>'

    with cols[i]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{info["name"]}</div>
            <div class="metric-ticker">{ticker.replace("=F","")}</div>
            <div class="metric-value">${fmt(price_d, 4)}</div>
            <div class="metric-unit">{info["unit"]}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

# ── Crush Spread ──────────────────────────────────────────────────────────────
st.markdown("")
zs = current["ZS=F"]
zl = current["ZL=F"]
zm = current["ZM=F"]
cs = crush_spread(zs, zl, zm)

# Prix convertis en $ pour l'affichage de la formule
zs_d = zs * 0.01 if zs else None
zl_d = zl * 0.01 if zl else None

crush_color = "positive" if (cs and cs >= 0) else "negative"
cs_str = f"${fmt(cs, 4)}/bss" if cs else "N/A"

cs_col1, cs_col2, cs_col3 = st.columns([1, 2, 1])
with cs_col2:
    st.markdown(f"""
    <div class="crush-card">
        <div class="crush-label">✦ Crush Spread</div>
        <div class="crush-value {crush_color}">{cs_str}</div>
        <div class="crush-formula">11 × {fmt(zl, 4)} + 0.022 × {fmt(zm, 2)} – {fmt(zs_d, 4)}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f'<p class="timestamp">Dernière mise à jour : {now_str}</p>', unsafe_allow_html=True)

# ── Historical chart ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Historique</p>', unsafe_allow_html=True)

try:
    df = hist.copy()
    df = df.dropna()

    # Conversion en dollars (ZS et ZL sont en ¢)
    df["ZS_d"] = df["ZS"] * 0.01
    df["ZL_d"] = df["ZL"] * 0.01
    # ZM déjà en $

    # Crush spread en $/boisseau
    df["Crush"] = 11 * (df["ZL"] / 100) + 0.022 * df["ZM"] - (df["ZS"] / 100)

    tab1, tab2 = st.tabs(["📊 Crush Spread", "📈 Prix individuels"])

    with tab1:
        fig_crush = go.Figure()
        fig_crush.add_trace(go.Scatter(
            x=df.index, y=df["Crush"],
            mode="lines",
            name="Crush Spread",
            line=dict(color="#f5c518", width=2),
            fill="tozeroy",
            fillcolor="rgba(245,197,24,0.07)"
        ))
        fig_crush.add_hline(y=0, line_dash="dash", line_color="#484f58", line_width=1)
        fig_crush.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Space Mono, monospace", color="#7d8590", size=11),
            xaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
            yaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d", title="$/boisseau"),
            margin=dict(l=10, r=10, t=20, b=10),
            hovermode="x unified",
            height=380,
        )
        st.plotly_chart(fig_crush, use_container_width=True)

    with tab2:
        fig2 = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=["ZS – Soja ($/bss)", "ZL – Huile de Soja ($/lb)", "ZM – Tourteau ($/t courte)"]
        )
        colors = ["#58a6ff", "#3fb950", "#f78166"]
        plot_cols = [("ZS_d", "ZS"), ("ZL_d", "ZL"), ("ZM", "ZM")]
        for row, ((col, label), color) in enumerate(zip(plot_cols, colors), start=1):
            fig2.add_trace(
                go.Scatter(x=df.index, y=df[col], mode="lines",
                           name=label, line=dict(color=color, width=1.5)),
                row=row, col=1
            )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Space Mono, monospace", color="#7d8590", size=10),
            showlegend=False,
            margin=dict(l=10, r=10, t=30, b=10),
            height=520,
        )
        for axis in ["xaxis", "xaxis2", "xaxis3", "yaxis", "yaxis2", "yaxis3"]:
            fig2.update_layout(**{axis: dict(gridcolor="#21262d", zerolinecolor="#21262d")})
        st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.warning(f"Impossible d'afficher l'historique : {e}")

# ── Stats table ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Statistiques sur la période</p>', unsafe_allow_html=True)

try:
    def fmtd(val, d=4): return f"${val:,.{d}f}" if val is not None else "N/A"
    stats_df = pd.DataFrame({
        "Contrat":    ["ZS – Soja ($/bss)", "ZL – Huile ($/lb)", "ZM – Tourteau ($/t)", "Crush Spread ($/bss)"],
        "Actuel":     [fmtd(zs_d), fmtd(zl_d), fmtd(zm, 2), fmtd(cs)],
        "Min":        [fmtd(df["ZS_d"].min()), fmtd(df["ZL_d"].min()), fmtd(df["ZM"].min(), 2), fmtd(df["Crush"].min())],
        "Max":        [fmtd(df["ZS_d"].max()), fmtd(df["ZL_d"].max()), fmtd(df["ZM"].max(), 2), fmtd(df["Crush"].max())],
        "Moy.":       [fmtd(df["ZS_d"].mean()), fmtd(df["ZL_d"].mean()), fmtd(df["ZM"].mean(), 2), fmtd(df["Crush"].mean())],
        "Écart-type": [fmtd(df["ZS_d"].std()), fmtd(df["ZL_d"].std()), fmtd(df["ZM"].std(), 2), fmtd(df["Crush"].std())],
    })
    st.dataframe(stats_df, use_container_width=True, hide_index=True)
except Exception:
    pass

# ── Stock-to-Use (USDA PSD API) ───────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Stock-to-Use ratio — USDA</p>', unsafe_allow_html=True)

@st.cache_data(ttl=3600*6)
def fetch_stu():
    """
    USDA FAS OpenData API — soja mondial (commodity 2222000, country all).
    """
    import requests
    rows = []
    for year in range(2010, datetime.now().year + 2):
        url = f"https://apps.fas.usda.gov/OpenData/api/psd/commodity/2222000/country/all/year/{year}"
        try:
            r = requests.get(url, timeout=15, headers={"Accept": "application/json"})
            if r.status_code != 200:
                continue
            data = r.json()
            for item in data:
                rows.append({
                    "year":        item.get("marketYear"),
                    "attributeId": item.get("attributeId"),
                    "value":       item.get("value"),
                    "countryCode": item.get("countryCode"),
                })
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    df_raw = pd.DataFrame(rows)
    # Garder seulement les données mondiales (countryCode = "00" ou agréger)
    # attributeId : 20=Production, 125=Total Dom. Consumption, 176=Total Use, 45=Ending Stocks
    df_world = df_raw[df_raw["attributeId"].isin([20, 176, 45])].copy()
    df_world = df_world.dropna(subset=["year", "value"])
    df_world["year"] = df_world["year"].astype(int)

    # Agréger par année + attribut (somme monde entier)
    df_pivot = df_world.groupby(["year", "attributeId"])["value"].sum().unstack("attributeId")
    df_pivot = df_pivot.rename(columns={20: "production", 176: "total_use", 45: "ending_stocks"})
    df_pivot = df_pivot.dropna()
    df_pivot["stu_pct"] = (df_pivot["ending_stocks"] / df_pivot["total_use"]) * 100
    df_pivot = df_pivot.sort_index()
    return df_pivot

try:
    df_stu = fetch_stu()
    if df_stu.empty:
        st.warning("Données USDA indisponibles.")
    else:
        col_stu1, col_stu2 = st.columns([2, 1])

        with col_stu1:
            fig_stu = go.Figure()
            # Barres STU
            colors_stu = ["#f85149" if v < 10 else "#f5c518" if v < 15 else "#3fb950"
                          for v in df_stu["stu_pct"]]
            fig_stu.add_trace(go.Bar(
                x=df_stu.index, y=df_stu["stu_pct"],
                name="Stock-to-Use (%)",
                marker_color=colors_stu,
                opacity=0.85,
            ))
            # Ligne seuil tendu
            fig_stu.add_hline(y=10, line_dash="dash", line_color="#f85149",
                              annotation_text="Seuil tendu 10%", annotation_font_color="#f85149")
            fig_stu.add_hline(y=15, line_dash="dot", line_color="#f5c518",
                              annotation_text="Seuil modéré 15%", annotation_font_color="#f5c518")
            fig_stu.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Space Mono, monospace", color="#7d8590", size=11),
                xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d", title="STU (%)"),
                margin=dict(l=10, r=10, t=20, b=10), height=320,
                hovermode="x unified",
            )
            st.plotly_chart(fig_stu, use_container_width=True)

        with col_stu2:
            last = df_stu.iloc[-1]
            stu_val  = last["stu_pct"]
            stu_color = "#f85149" if stu_val < 10 else "#f5c518" if stu_val < 15 else "#3fb950"
            stu_label = "🔴 TENDU" if stu_val < 10 else "🟡 MODÉRÉ" if stu_val < 15 else "🟢 CONFORTABLE"
            st.markdown(f"""
            <div class="metric-card" style="margin-top:10px">
                <div class="metric-label">STU Mondial {int(df_stu.index[-1])}/{int(df_stu.index[-1])+1}</div>
                <div class="metric-value" style="color:{stu_color}">{stu_val:.1f}%</div>
                <div class="metric-unit">{stu_label}</div>
                <br>
                <div class="metric-unit">Production : {last['production']:.0f} Mt</div>
                <div class="metric-unit">Consommation : {last['total_use']:.0f} Mt</div>
                <div class="metric-unit">Stocks fin : {last['ending_stocks']:.0f} Mt</div>
            </div>
            """, unsafe_allow_html=True)

except Exception as e:
    st.warning(f"Impossible de charger les données USDA : {e}")


# ── BRL/USD + corrélation ZS ──────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Compétitivité Brésil — BRL/USD vs ZS</p>', unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_brl(period="1y"):
    brl = yf.Ticker("BRL=X").history(period=period, auto_adjust=True)["Close"].dropna()
    # BRL=X = USD par BRL, on veut BRL par USD
    return (1 / brl).rename("USDBRL")

try:
    df_brl = fetch_brl(period)
    # Récupérer ZS sur la même période depuis hist déjà chargé
    df_zs_hist = hist[["ZS"]].copy().dropna()
    df_zs_hist["ZS_d"] = df_zs_hist["ZS"] * 0.01

    # Aligner les deux séries sur les dates communes
    df_fx = pd.DataFrame(df_brl)
    df_fx.index = df_fx.index.tz_localize(None)
    df_zs_hist.index = df_zs_hist.index.tz_localize(None) if df_zs_hist.index.tz else df_zs_hist.index
    df_merged = df_fx.join(df_zs_hist["ZS_d"], how="inner")

    fig_brl = make_subplots(specs=[[{"secondary_y": True}]])
    fig_brl.add_trace(go.Scatter(
        x=df_merged.index, y=df_merged["USDBRL"],
        name="USD/BRL", line=dict(color="#f5c518", width=1.8)
    ), secondary_y=False)
    fig_brl.add_trace(go.Scatter(
        x=df_merged.index, y=df_merged["ZS_d"],
        name="ZS ($/bss)", line=dict(color="#58a6ff", width=1.8)
    ), secondary_y=True)

    fig_brl.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Mono, monospace", color="#7d8590", size=11),
        xaxis=dict(gridcolor="#21262d"),
        margin=dict(l=10, r=10, t=20, b=10), height=320,
        hovermode="x unified",
        legend=dict(bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99),
    )
    fig_brl.update_yaxes(title_text="USD/BRL", gridcolor="#21262d", secondary_y=False)
    fig_brl.update_yaxes(title_text="ZS $/bss", gridcolor="#21262d", secondary_y=True)
    st.plotly_chart(fig_brl, use_container_width=True)

    # Corrélation glissante 60j
    if len(df_merged) >= 60:
        df_merged["corr_60"] = df_merged["USDBRL"].rolling(60).corr(df_merged["ZS_d"])
        fig_corr = go.Figure()
        fig_corr.add_trace(go.Scatter(
            x=df_merged.index, y=df_merged["corr_60"],
            mode="lines", name="Corrélation 60j",
            line=dict(color="#3fb950", width=1.5),
            fill="tozeroy", fillcolor="rgba(63,185,80,0.07)"
        ))
        fig_corr.add_hline(y=0, line_color="#484f58", line_width=1)
        fig_corr.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Space Mono, monospace", color="#7d8590", size=11),
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(gridcolor="#21262d", title="Corrélation", range=[-1, 1]),
            margin=dict(l=10, r=10, t=10, b=10), height=200,
        )
        st.caption("📊 Corrélation glissante 60j entre USD/BRL et ZS — proche de +1 = le BRL suit le soja")
        st.plotly_chart(fig_corr, use_container_width=True)

except Exception as e:
    st.warning(f"Impossible de charger BRL/USD : {e}")


# ── Export Sales US (USDA) ────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Export Sales US — USDA</p>', unsafe_allow_html=True)

@st.cache_data(ttl=3600*6)
def fetch_export_sales():
    """
    USDA FAS OpenData API — Export Sales hebdomadaires soja US
    commodity 2222000, unité 1000 MT
    """
    import requests
    from datetime import date, timedelta
    end   = date.today()
    start = end - timedelta(days=365)
    url = (
        f"https://apps.fas.usda.gov/OpenData/api/esr/exports"
        f"?commodityCode=2222000"
        f"&countryCode=0000"
        f"&startDate={start}&endDate={end}"
    )
    r = requests.get(url, timeout=15, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()

    rows = []
    for item in data:
        rows.append({
            "week":         item.get("weeklyExportSalesDate") or item.get("reportDate") or item.get("weekEndingDate"),
            "net_sales_mt": item.get("netSalesMT") or item.get("netSales1516") or item.get("currentMYNetSales"),
            "exports_mt":   item.get("exportsMT") or item.get("exports1516") or item.get("currentMYExports"),
        })
    df = pd.DataFrame(rows).dropna(subset=["week"])
    df["week"] = pd.to_datetime(df["week"])
    df = df.sort_values("week").tail(52)
    return df

try:
    df_exp = fetch_export_sales()
    if df_exp.empty:
        st.info("Données d'export sales non disponibles.")
    else:
        fig_exp = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                vertical_spacing=0.08,
                                subplot_titles=["Ventes nettes (1000 MT)", "Exports réels (1000 MT)"])
        fig_exp.add_trace(go.Bar(
            x=df_exp["week"], y=df_exp["net_sales_mt"],
            name="Ventes nettes", marker_color="#58a6ff", opacity=0.8
        ), row=1, col=1)
        fig_exp.add_trace(go.Bar(
            x=df_exp["week"], y=df_exp["exports_mt"],
            name="Exports réels", marker_color="#3fb950", opacity=0.8
        ), row=2, col=1)
        fig_exp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Space Mono, monospace", color="#7d8590", size=11),
            showlegend=False,
            margin=dict(l=10, r=10, t=30, b=10), height=400,
        )
        for axis in ["xaxis", "xaxis2", "yaxis", "yaxis2"]:
            fig_exp.update_layout(**{axis: dict(gridcolor="#21262d")})
        st.plotly_chart(fig_exp, use_container_width=True)
        st.caption("Source : USDA Export Sales Reporting — données hebdomadaires")

except Exception as e:
    st.info(f"Export sales USDA : {e}")


# ── Basis manuel ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Basis (saisie manuelle)</p>', unsafe_allow_html=True)

spot_price = st.sidebar.number_input(
    "Prix spot local ($/bss)",
    min_value=0.0, max_value=50.0,
    value=0.0, step=0.01,
    format="%.4f",
    help="Entrez votre prix spot physique local en $/boisseau"
)

if spot_price > 0 and zs is not None:
    basis = spot_price - (zs / 100)
    basis_color = "#3fb950" if basis >= 0 else "#f85149"
    basis_label = "prime" if basis >= 0 else "décote"
    b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
    with b_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Basis — {basis_label} sur le CBOT</div>
            <div class="metric-value" style="color:{basis_color}">${basis:+.4f}/bss</div>
            <div class="metric-unit">Spot {spot_price:.4f} − Futures {zs/100:.4f}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 Entrez votre prix spot local dans la sidebar pour calculer le basis.")


# ── Auto refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
