from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.cache import fetch_index_prices, fetch_stock_prices
from data.prices import daily_returns
from ui.components import kpi_card
from ui.theme import fund_color, inject_css, plotly_layout

st.set_page_config(page_title="Portföy Simülasyonu", page_icon="💼", layout="wide")
inject_css()

st.title("Portföy Simülasyonu")
st.caption("Hisse ağırlıklarını gir, geçmiş performansı XU100 endeksine göre kıyasla")

with st.sidebar:
    st.subheader("Portföy")
    default_rows = pd.DataFrame({"Sembol": ["THYAO", "ASELS", "EREGL"], "Ağırlık (%)": [40.0, 30.0, 30.0]})
    portfolio_df = st.data_editor(
        default_rows,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio_editor",
    )

    st.subheader("Dönem")
    end = st.date_input("Bitiş", value=date.today(), key="portfolio_end")
    start = st.date_input("Başlangıç", value=date.today() - timedelta(days=365), key="portfolio_start")

portfolio_df = portfolio_df.dropna(subset=["Sembol"])
portfolio_df["Sembol"] = portfolio_df["Sembol"].astype(str).str.strip().str.upper()
portfolio_df = portfolio_df[portfolio_df["Sembol"] != ""]

if portfolio_df.empty:
    st.info("Başlamak için en az bir hisse ve ağırlık girin.")
    st.stop()

if start >= end:
    st.error("Başlangıç tarihi bitiş tarihinden önce olmalı.")
    st.stop()

weight_sum = portfolio_df["Ağırlık (%)"].sum()
if weight_sum <= 0:
    st.error("Ağırlıkların toplamı sıfırdan büyük olmalı.")
    st.stop()
portfolio_df["Ağırlık"] = portfolio_df["Ağırlık (%)"] / weight_sum

symbols = portfolio_df["Sembol"].tolist()

with st.spinner("Fiyat verisi çekiliyor..."):
    try:
        price_df = fetch_stock_prices(symbols, start, end)
    except ValueError as exc:
        st.error(f"Veri çekilemedi: {exc}")
        st.stop()
    try:
        index_df = fetch_index_prices("XU100", start, end)
    except ValueError:
        index_df = pd.DataFrame()

returns_by_symbol = {}
missing = []
for sym in symbols:
    r = daily_returns(price_df, sym)
    if r.empty:
        missing.append(sym)
        continue
    returns_by_symbol[sym] = r

for sym in missing:
    st.warning(f"{sym}: fiyat verisi bulunamadı, portföy hesabına dahil edilmedi")

if not returns_by_symbol:
    st.error("Hiçbir sembol için veri alınamadı.")
    st.stop()

returns_wide = pd.DataFrame(returns_by_symbol).dropna(how="all")
weights = portfolio_df.set_index("Sembol")["Ağırlık"].reindex(returns_wide.columns).fillna(0)
weights = weights / weights.sum()

portfolio_returns = (returns_wide.fillna(0) * weights).sum(axis=1)
portfolio_cumulative = (1 + portfolio_returns).cumprod() - 1

# --- KPI'lar --------------------------------------------------------------
total_return = portfolio_cumulative.iloc[-1] * 100
annualized_vol = portfolio_returns.std() * np.sqrt(252) * 100
running_max = (1 + portfolio_returns).cumprod().cummax()
drawdown = ((1 + portfolio_returns).cumprod() / running_max - 1).min() * 100
sharpe = (portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)) if portfolio_returns.std() > 0 else 0

cols = st.columns(4)
with cols[0]:
    kpi_card("Toplam Getiri", f"{total_return:+.1f}%", delta_good=total_return >= 0)
with cols[1]:
    kpi_card("Yıllıklandırılmış Volatilite", f"{annualized_vol:.1f}%")
with cols[2]:
    kpi_card("Maksimum Düşüş (Drawdown)", f"{drawdown:.1f}%", delta_good=False)
with cols[3]:
    kpi_card("Sharpe (risksiz oran=0)", f"{sharpe:.2f}", delta_good=sharpe >= 0)

st.divider()

# --- Kümülatif getiri grafiği ---------------------------------------------
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        name="Portföy",
        x=portfolio_cumulative.index,
        y=portfolio_cumulative.values * 100,
        mode="lines",
        line=dict(color=fund_color(0), width=3),
    )
)

if not index_df.empty:
    index_df = index_df.sort_values("DATE")
    index_returns = index_df.set_index("DATE")["VALUE"].pct_change().dropna()
    index_cumulative = (1 + index_returns).cumprod() - 1
    fig.add_trace(
        go.Scatter(
            name="XU100",
            x=index_cumulative.index,
            y=index_cumulative.values * 100,
            mode="lines",
            line=dict(color=fund_color(1), width=2, dash="dot"),
        )
    )

fig.update_layout(**plotly_layout(title="Kümülatif Getiri (%)", yaxis_title="Getiri (%)"))
st.plotly_chart(fig, use_container_width=True)

with st.expander("Portföy ağırlıkları"):
    st.dataframe(
        portfolio_df[["Sembol", "Ağırlık"]].assign(**{"Ağırlık (%)": lambda d: d["Ağırlık"] * 100}).drop(columns="Ağırlık"),
        use_container_width=True,
    )
