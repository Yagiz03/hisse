from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.cache import fetch_financials
from data.financials import latest_value, metric_series
from ui.components import download_excel_button, kpi_card
from ui.nav import top_nav
from ui.theme import fund_color, inject_css, plotly_layout

st.set_page_config(page_title="Finansal Tablolar", page_icon="📈", layout="wide")
inject_css()
top_nav("Finansal Tablolar")

st.title("Finansal Tablolar")
st.caption("BIST şirketlerinin bilanço / gelir tablosu kalemlerini karşılaştırın (kaynak: İş Yatırım)")

with st.sidebar:
    st.subheader("Şirket Seçimi")
    symbols_input = st.text_input(
        "Hisse kodları (virgülle ayırın)",
        placeholder="Örn: THYAO, ASELS, EREGL",
    )
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

    st.subheader("Dönem")
    current_year = date.today().year
    start_year = st.number_input("Başlangıç yılı", min_value=2010, max_value=current_year, value=current_year - 2)
    end_year = st.number_input("Bitiş yılı", min_value=2010, max_value=current_year, value=current_year)

    st.subheader("Ayarlar")
    exchange = st.radio("Para birimi", ["TRY", "USD"], horizontal=True)
    group_label = st.selectbox("Finansal grup", ["XI_29", "UFRS", "UFRS_K"])
    financial_group = {"XI_29": "1", "UFRS": "2", "UFRS_K": "3"}[group_label]

if not symbols:
    st.info("Başlamak için en az bir hisse kodu girin (karşılaştırma için birden fazla önerilir).")
    st.stop()

if start_year > end_year:
    st.error("Başlangıç yılı bitiş yılından büyük olamaz.")
    st.stop()

with st.spinner("İş Yatırım'dan finansal tablolar çekiliyor..."):
    try:
        df = fetch_financials(symbols, int(start_year), int(end_year), exchange, financial_group)
    except ValueError as exc:
        st.error(f"Veri çekilemedi: {exc}")
        st.stop()

available_symbols = [s for s in symbols if s in df["SYMBOL"].unique()]
missing_symbols = [s for s in symbols if s not in available_symbols]
for s in missing_symbols:
    st.warning(f"{s}: finansal veri bulunamadı (sembol/yıl aralığını kontrol edin)")

if not available_symbols:
    st.stop()

# --- KPI kartları (son çeyrek) -----------------------------------------
cols = st.columns(len(available_symbols))
for i, sym in enumerate(available_symbols):
    with cols[i]:
        revenue = latest_value(df, sym, "Hasılat")
        net_income = latest_value(df, sym, "Net Dönem Karı")
        kpi_card(f"{sym} · Son Çeyrek Hasılat", f"{revenue:,.0f}" if revenue is not None else "veri yok")
        kpi_card(f"{sym} · Son Çeyrek Net Kar", f"{net_income:,.0f}" if net_income is not None else "veri yok")

st.divider()

# --- Trend grafiği: Hasılat ve Net Kar ----------------------------------
st.subheader("Hasılat ve Net Kar Trendi")
metric_choice = st.radio("Metrik", ["Hasılat", "Net Dönem Karı"], horizontal=True)

fig = go.Figure()
for i, sym in enumerate(available_symbols):
    series = metric_series(df, sym, metric_choice)
    if series.empty:
        continue
    fig.add_trace(
        go.Scatter(
            name=sym,
            x=list(series.index),
            y=list(series.values),
            mode="lines+markers",
            line=dict(color=fund_color(i), width=2),
            marker=dict(size=8),
        )
    )
fig.update_layout(**plotly_layout(title=f"{metric_choice} ({exchange})", yaxis_title=metric_choice))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Oran paneli (son çeyrek) --------------------------------------------
st.subheader("Rasyo Karşılaştırması (Son Çeyrek)")

rows = []
for sym in available_symbols:
    donen = latest_value(df, sym, "Dönen Varlıklar")
    kv_yukumluluk = latest_value(df, sym, "Kısa Vadeli Yükümlülükler")
    toplam_yukumluluk = latest_value(df, sym, "Toplam Yükümlülükler")
    ozkaynak = latest_value(df, sym, "Özkaynaklar")
    net_kar = latest_value(df, sym, "Net Dönem Karı")

    cari_oran = donen / kv_yukumluluk if donen and kv_yukumluluk else None
    borc_ozkaynak = toplam_yukumluluk / ozkaynak if toplam_yukumluluk and ozkaynak else None
    roe = net_kar / ozkaynak if net_kar and ozkaynak else None

    rows.append(
        {
            "Sembol": sym,
            "Cari Oran": cari_oran,
            "Borç / Özkaynak": borc_ozkaynak,
            "ROE (Çeyreklik)": roe,
        }
    )

ratio_df = pd.DataFrame(rows).set_index("Sembol")
st.dataframe(ratio_df.style.format("{:.2f}", na_rep="-"), use_container_width=True)
st.caption("ROE burada yıllıklandırılmamış, tek çeyreğin net kar / özkaynak oranıdır.")

with st.expander("Ham finansal tablo verisi"):
    st.dataframe(df, use_container_width=True)

download_excel_button(df, "finansal_tablolar.xlsx")
