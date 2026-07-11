"""Ortak Streamlit UI bileşenleri (KPI kartı vb.)."""

import streamlit as st


def kpi_card(label: str, value: str, delta: str | None = None, delta_good: bool = True) -> None:
    delta_html = ""
    if delta:
        cls = "kpi-delta-good" if delta_good else "kpi-delta-bad"
        delta_html = f'<div class="{cls}">{delta}</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
