"""Ortak Streamlit UI bileşenleri (KPI kartı vb.)."""

from io import BytesIO

import pandas as pd
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


def download_excel_button(df: pd.DataFrame, file_name: str, label: str = "Excel'e aktar") -> None:
    buffer = BytesIO()
    df.to_excel(buffer, index=True)
    st.download_button(
        label=label,
        data=buffer.getvalue(),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
