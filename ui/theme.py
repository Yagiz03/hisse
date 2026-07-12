"""Koyu tema renk paleti ve ortak Streamlit/Plotly stil yardımcıları."""

import streamlit as st

# Sabit sıralı kategorik palet (fon/entity kimliği için) - dark surface üzerinde
# doğrulanmış (validate_palette.js), sıra değiştirilmemeli.
CATEGORICAL = [
    "#3987e5",  # blue
    "#199e70",  # aqua
    "#c98500",  # yellow
    "#008300",  # green
    "#9085e9",  # violet
    "#e66767",  # red
    "#d55181",  # magenta
    "#d95926",  # orange
]

STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

SURFACE = "#1a1a19"
PAGE_PLANE = "#0d0d0d"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#c3c2b7"
TEXT_MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BASELINE = "#383835"


def fund_color(index: int) -> str:
    """Seçilen fonlara, seçim sırasına göre sabit bir renk atar."""
    return CATEGORICAL[index % len(CATEGORICAL)]


def plotly_layout(**overrides) -> dict:
    """Plotly grafikleri için ortak koyu tema layout'u."""
    layout = dict(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=TEXT_PRIMARY, family="system-ui, -apple-system, 'Segoe UI', sans-serif"),
        legend=dict(font=dict(color=TEXT_SECONDARY)),
        xaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, tickfont=dict(color=TEXT_MUTED)),
        yaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, tickfont=dict(color=TEXT_MUTED)),
        margin=dict(l=40, r=20, t=40, b=40),
    )
    layout.update(overrides)
    return layout


def inject_css() -> None:
    accent_gradient = f"linear-gradient(90deg, {CATEGORICAL[0]}, {CATEGORICAL[4]}, {CATEGORICAL[7]})"
    st.markdown(
        f"""
        <style>
        /* Varsayılan çok sayfalı sidebar listesini gizle - navigasyonu üstteki
           pill-tab menü (ui/nav.py) devralıyor. */
        [data-testid="stSidebarNav"] {{ display: none; }}

        .kpi-card {{
            position: relative;
            background: {SURFACE};
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            padding: 18px 20px 16px;
            margin-bottom: 8px;
            overflow: hidden;
        }}
        .kpi-card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: {accent_gradient};
        }}
        .kpi-label {{
            color: {TEXT_MUTED};
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .kpi-value {{
            color: {TEXT_PRIMARY};
            font-size: 1.7rem;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            margin-top: 4px;
        }}
        .kpi-delta-good {{ color: {STATUS['good']}; font-size: 0.85rem; }}
        .kpi-delta-bad {{ color: {STATUS['critical']}; font-size: 0.85rem; }}
        .kpi-value-good {{ color: {STATUS['good']}; }}
        .kpi-value-bad {{ color: {STATUS['critical']}; }}

        section[data-testid="stSidebar"] {{
            background: {SURFACE};
            border-right: 1px solid rgba(255,255,255,0.08);
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
        }}

        .stButton > button, .stDownloadButton > button {{
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.15);
        }}

        h1 {{
            background: {accent_gradient};
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
