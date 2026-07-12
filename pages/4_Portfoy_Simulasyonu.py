from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.cache import fetch_index_prices, fetch_stock_prices
from data.prices import daily_returns
from ui.components import download_excel_button, kpi_card
from ui.theme import fund_color, plotly_layout

st.title("Portföy Simülasyonu")
st.caption("Hisse ağırlıklarını gir, geçmiş performansı XU100 endeksine göre kıyasla")

with st.container(border=True):
    col_editor, col_dates = st.columns([2, 1])
    with col_editor:
        st.caption("Portföy")
        default_rows = pd.DataFrame({"Sembol": ["THYAO", "ASELS", "EREGL"], "Ağırlık (%)": [40.0, 30.0, 30.0]})
        portfolio_df = st.data_editor(
            default_rows,
            num_rows="dynamic",
            use_container_width=True,
            key="portfolio_editor",
        )
    with col_dates:
        st.caption("Dönem")
        start = st.date_input("Başlangıç", value=date.today() - timedelta(days=365), key="portfolio_start")
        end = st.date_input("Bitiş", value=date.today(), key="portfolio_end")

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

win_rate = (portfolio_returns > 0).mean() * 100
best_day = portfolio_returns.max() * 100
worst_day = portfolio_returns.min() * 100

cols = st.columns(4)
with cols[0]:
    kpi_card("Toplam Getiri", f"{total_return:+.1f}%", delta_good=total_return >= 0)
with cols[1]:
    kpi_card("Yıllıklandırılmış Volatilite", f"{annualized_vol:.1f}%")
with cols[2]:
    kpi_card("Maksimum Düşüş (Drawdown)", f"{drawdown:.1f}%", delta_good=False)
with cols[3]:
    kpi_card("Sharpe (risksiz oran=0)", f"{sharpe:.2f}", delta_good=sharpe >= 0)

cols2 = st.columns(4)
with cols2[0]:
    kpi_card("Kazanma Oranı", f"%{win_rate:.0f}", delta_good=win_rate >= 50)
with cols2[1]:
    kpi_card("En İyi Gün", f"{best_day:+.1f}%", delta_good=True)
with cols2[2]:
    kpi_card("En Kötü Gün", f"{worst_day:+.1f}%", delta_good=False)
with cols2[3]:
    if not index_df.empty:
        index_df_sorted = index_df.sort_values("DATE")
        index_total_return = (
            index_df_sorted["VALUE"].iloc[-1] / index_df_sorted["VALUE"].iloc[0] - 1
        ) * 100
        alpha = total_return - index_total_return
        kpi_card("XU100'e Göre Fark", f"{alpha:+.1f}%", delta_good=alpha >= 0)
    else:
        kpi_card("XU100'e Göre Fark", "veri yok")

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

if len(returns_wide.columns) > 1:
    st.divider()
    st.subheader("Korelasyon Matrisi")
    st.caption("Portföydeki hisselerin günlük getirileri arasındaki korelasyon - birbirine yakın hareket eden hisseler çeşitlendirme faydasını azaltır")
    corr = returns_wide.corr()
    corr_fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale=[[0, "#e66767"], [0.5, "#383835"], [1, "#3987e5"]],
            zmin=-1,
            zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            textfont=dict(color="#ffffff"),
        )
    )
    corr_fig.update_layout(**plotly_layout(title="Korelasyon Matrisi", margin=dict(l=40, r=20, t=40, b=40)))
    st.plotly_chart(corr_fig, use_container_width=True)

st.divider()

weights_display = (
    portfolio_df[["Sembol", "Ağırlık"]]
    .assign(**{"Ağırlık (%)": lambda d: d["Ağırlık"] * 100})
    .drop(columns="Ağırlık")
    .set_index("Sembol")
)
with st.expander("Portföy ağırlıkları"):
    st.dataframe(weights_display, use_container_width=True)

download_excel_button(portfolio_cumulative.to_frame("Kümülatif Getiri"), "portfoy_simulasyonu.xlsx")
