from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from data.cache import fetch_stock_prices
from data.prices import period_return
from data.sectors import BIST30_SECTORS
from ui.components import download_excel_button, kpi_card
from ui.nav import top_nav
from ui.theme import SURFACE, TEXT_PRIMARY, plotly_layout, inject_css

st.set_page_config(page_title="Sektör Isı Haritası", page_icon="🗺️", layout="wide")
inject_css()
top_nav("Sektör Isı Haritası")

st.title("Sektör Isı Haritası")
st.caption("BIST30 şirketlerinin seçilen dönemdeki getirisi, sektöre göre gruplanmış (kaynak: İş Yatırım)")

with st.sidebar:
    st.subheader("Dönem")
    end = st.date_input("Bitiş", value=date.today(), key="heatmap_end")
    start = st.date_input("Başlangıç", value=date.today() - timedelta(days=7), key="heatmap_start")

if start >= end:
    st.error("Başlangıç tarihi bitiş tarihinden önce olmalı.")
    st.stop()

symbols = list(BIST30_SECTORS.keys())

with st.spinner("Fiyat verisi çekiliyor..."):
    try:
        df = fetch_stock_prices(symbols, start, end)
    except ValueError as exc:
        st.error(f"Veri çekilemedi: {exc}")
        st.stop()

rows = []
for sym in symbols:
    ret = period_return(df, sym)
    if ret is None:
        continue
    rows.append({"Sembol": sym, "Sektör": BIST30_SECTORS[sym], "Getiri": ret})

if not rows:
    st.warning("Seçilen aralık için veri bulunamadı.")
    st.stop()

heat_df = pd.DataFrame(rows)
max_abs = max(heat_df["Getiri"].abs().max(), 1e-6)

# --- KPI kartları ---------------------------------------------------------
best = heat_df.loc[heat_df["Getiri"].idxmax()]
worst = heat_df.loc[heat_df["Getiri"].idxmin()]
cols = st.columns(4)
with cols[0]:
    kpi_card("Ortalama Getiri", f"{heat_df['Getiri'].mean():+.2f}%", delta_good=heat_df["Getiri"].mean() >= 0)
with cols[1]:
    kpi_card("Yükselen / Düşen", f"{(heat_df['Getiri'] > 0).sum()} / {(heat_df['Getiri'] < 0).sum()}")
with cols[2]:
    kpi_card(f"En Güçlü: {best['Sembol']}", f"{best['Getiri']:+.2f}%", delta_good=True)
with cols[3]:
    kpi_card(f"En Zayıf: {worst['Sembol']}", f"{worst['Getiri']:+.2f}%", delta_good=False)

st.divider()

fig = px.treemap(
    heat_df,
    path=[px.Constant("BIST30"), "Sektör", "Sembol"],
    values=[1] * len(heat_df),
    color="Getiri",
    color_continuous_scale=["#e66767", "#383835", "#3987e5"],
    range_color=[-max_abs, max_abs],
    custom_data=["Getiri"],
)
fig.update_traces(
    texttemplate="<b>%{label}</b><br>%{customdata[0]:.1f}%",
    textfont=dict(color=TEXT_PRIMARY),
    marker=dict(line=dict(color=SURFACE, width=2)),
)
fig.update_layout(**plotly_layout(title=f"{start:%d.%m.%Y} - {end:%d.%m.%Y} Getiri (%)", margin=dict(l=10, r=10, t=40, b=10)))
fig.update_coloraxes(colorbar=dict(title="% Değişim", tickfont=dict(color=TEXT_PRIMARY)))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- En çok yükselen / düşen ----------------------------------------------
top_n = min(5, len(heat_df))
col_gain, col_lose = st.columns(2)
with col_gain:
    st.subheader("En Çok Yükselenler")
    gainers = heat_df.sort_values("Getiri", ascending=False).head(top_n).set_index("Sembol")
    st.dataframe(gainers.style.format({"Getiri": "{:+.2f}%"}), use_container_width=True)
with col_lose:
    st.subheader("En Çok Düşenler")
    losers = heat_df.sort_values("Getiri", ascending=True).head(top_n).set_index("Sembol")
    st.dataframe(losers.style.format({"Getiri": "{:+.2f}%"}), use_container_width=True)

st.divider()

# --- Sektör ortalamaları ---------------------------------------------------
st.subheader("Sektör Ortalamaları")
sector_avg = heat_df.groupby("Sektör")["Getiri"].agg(["mean", "count"]).rename(
    columns={"mean": "Ortalama Getiri", "count": "Şirket Sayısı"}
).sort_values("Ortalama Getiri", ascending=False)
st.dataframe(sector_avg.style.format({"Ortalama Getiri": "{:+.2f}%"}), use_container_width=True)

with st.expander("Tablo görünümü (tüm şirketler)"):
    st.dataframe(
        heat_df.sort_values("Getiri", ascending=False).style.format({"Getiri": "{:+.2f}%"}),
        use_container_width=True,
    )

download_excel_button(heat_df.set_index("Sembol"), "sektor_isi_haritasi.xlsx")
