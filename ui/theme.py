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
    st.markdown(
        f"""
        <style>
        .kpi-card {{
            background: {SURFACE};
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 8px;
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
        }}
        .kpi-delta-good {{ color: {STATUS['good']}; font-size: 0.85rem; }}
        .kpi-delta-bad {{ color: {STATUS['critical']}; font-size: 0.85rem; }}
        section[data-testid="stSidebar"] {{
            background: {SURFACE};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
