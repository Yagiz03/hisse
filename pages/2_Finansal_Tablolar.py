from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.cache import fetch_financials
from data.financials import latest_value, metric_series, pivot_symbol_table, qoq_growth
from ui.components import download_excel_button, kpi_card
from ui.nav import top_nav
from ui.theme import fund_color, inject_css, plotly_layout

st.set_page_config(page_title="Finansal Tablolar", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
inject_css()
top_nav("Finansal Tablolar")

st.title("Finansal Tablolar")
st.caption("BIST şirketlerinin bilanço / gelir tablosu kalemlerini karşılaştırın (kaynak: İş Yatırım)")

with st.container(border=True):
    symbols_input = st.text_input(
        "Hisse kodları (virgülle ayırın)",
        placeholder="Örn: THYAO, ASELS, EREGL",
    )
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

    current_year = date.today().year
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        start_year = st.number_input("Başlangıç yılı", min_value=2010, max_value=current_year, value=current_year - 2)
    with c2:
        end_year = st.number_input("Bitiş yılı", min_value=2010, max_value=current_year, value=current_year)
    with c3:
        exchange = st.radio("Para birimi", ["TRY", "USD"], horizontal=True)
    with c4:
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

# --- KPI kartları (son çeyrek, çeyreklik büyüme ile) --------------------
cols = st.columns(len(available_symbols))
for i, sym in enumerate(available_symbols):
    with cols[i]:
        st.markdown(f"**{sym}**")
        revenue = latest_value(df, sym, "Hasılat")
        revenue_g = qoq_growth(df, sym, "Hasılat")
        kpi_card(
            "Hasılat (Son Çeyrek)",
            f"{revenue:,.0f}" if revenue is not None else "veri yok",
            delta=f"{revenue_g:+.1f}% ÇÇ" if revenue_g is not None else None,
            delta_good=(revenue_g >= 0) if revenue_g is not None else None,
        )
        net_income = latest_value(df, sym, "Net Dönem Karı")
        net_income_g = qoq_growth(df, sym, "Net Dönem Karı")
        kpi_card(
            "Net Kar (Son Çeyrek)",
            f"{net_income:,.0f}" if net_income is not None else "veri yok",
            delta=f"{net_income_g:+.1f}% ÇÇ" if net_income_g is not None else None,
            delta_good=(net_income_g >= 0) if net_income_g is not None else None,
        )

st.divider()

# --- Trend grafiği: Hasılat ve Net Kar ----------------------------------
st.subheader("Trend")
metric_choice = st.radio(
    "Metrik", ["Hasılat", "Esas Faaliyet Karı", "Net Dönem Karı", "Toplam Varlıklar"], horizontal=True
)

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
    hasilat = latest_value(df, sym, "Hasılat")
    faaliyet_kari = latest_value(df, sym, "Esas Faaliyet Karı")
    net_kar = latest_value(df, sym, "Net Dönem Karı")
    donen = latest_value(df, sym, "Dönen Varlıklar")
    kv_yukumluluk = latest_value(df, sym, "Kısa Vadeli Yükümlülükler")
    toplam_varlik = latest_value(df, sym, "Toplam Varlıklar")
    toplam_yukumluluk = latest_value(df, sym, "Toplam Yükümlülükler")
    ozkaynak = latest_value(df, sym, "Özkaynaklar")

    rows.append(
        {
            "Sembol": sym,
            "Cari Oran": donen / kv_yukumluluk if donen and kv_yukumluluk else None,
            "Borç / Özkaynak": toplam_yukumluluk / ozkaynak if toplam_yukumluluk and ozkaynak else None,
            "Borçluluk Oranı (%)": (toplam_yukumluluk / toplam_varlik * 100) if toplam_yukumluluk and toplam_varlik else None,
            "Faaliyet Kar Marjı (%)": (faaliyet_kari / hasilat * 100) if faaliyet_kari and hasilat else None,
            "Net Kar Marjı (%)": (net_kar / hasilat * 100) if net_kar and hasilat else None,
            "ROE (Çeyreklik, %)": (net_kar / ozkaynak * 100) if net_kar and ozkaynak else None,
            "ROA (Çeyreklik, %)": (net_kar / toplam_varlik * 100) if net_kar and toplam_varlik else None,
        }
    )

ratio_df = pd.DataFrame(rows).set_index("Sembol")
st.dataframe(ratio_df.style.format("{:.2f}", na_rep="-"), use_container_width=True)
st.caption("ROE ve ROA burada yıllıklandırılmamıştır, tek çeyreğin oranıdır.")

st.divider()

# --- Tam finansal tablo (şirket bazlı) -----------------------------------
st.subheader("Tam Finansal Tablo")
tabs = st.tabs(available_symbols)
for sym, tab in zip(available_symbols, tabs):
    with tab:
        pivot = pivot_symbol_table(df, sym)
        if pivot.empty:
            st.info("Bu şirket için detaylı tablo verisi yok.")
            continue
        st.dataframe(pivot.style.format("{:,.0f}", na_rep="-"), use_container_width=True, height=420)
        download_excel_button(pivot, f"{sym}_finansal_tablo.xlsx", label=f"{sym} tablosunu indir")

with st.expander("Ham finansal tablo verisi (tüm şirketler)"):
    st.dataframe(df, use_container_width=True)

download_excel_button(df, "finansal_tablolar.xlsx")
