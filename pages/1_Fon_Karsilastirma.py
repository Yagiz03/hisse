from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.cache import fetch_allocation, fetch_info
from data.tefas import TefasError
from ui.components import download_excel_button, kpi_card
from ui.theme import fund_color, inject_css, plotly_layout

st.set_page_config(page_title="Fon Karşılaştırma", page_icon="📊", layout="wide")
inject_css()

st.title("Fon Karşılaştırma")
st.caption("Fon kodlarını girin, varlık dağılımlarını ve farklarını karşılaştırın")

with st.sidebar:
    st.subheader("Fon Seçimi")
    codes_input = st.text_input(
        "Fon kodları (virgülle ayırın)",
        placeholder="Örn: TTE, AFT, IPB",
    )
    fund_codes = [c.strip().upper() for c in codes_input.split(",") if c.strip()]

    st.subheader("Tarih Aralığı")
    end_date = st.date_input("Bitiş", value=date.today())
    start_date = st.date_input("Başlangıç", value=date.today() - timedelta(days=30))

if not fund_codes:
    st.info("Karşılaştırmaya başlamak için en az iki fon kodu girin.")
    st.stop()

if len(fund_codes) < 2:
    st.warning("Karşılaştırma için en az iki fon kodu gerekli.")
    st.stop()

if start_date >= end_date:
    st.error("Başlangıç tarihi bitiş tarihinden önce olmalı.")
    st.stop()

allocations: dict[str, dict[str, float]] = {}
info_rows: dict[str, pd.Series] = {}
errors: list[str] = []

with st.spinner("TEFAS'tan veri çekiliyor..."):
    for code in fund_codes:
        try:
            alloc_df = fetch_allocation(code, start_date, end_date)
            if alloc_df.empty:
                errors.append(f"{code}: dağılım verisi bulunamadı (kod/tarih aralığını kontrol edin)")
                continue
            last_row = alloc_df.iloc[-1]
            allocations[code] = {
                col: float(last_row[col])
                for col in alloc_df.columns
                if col not in ("TARIH", "FONKODU")
                and pd.api.types.is_numeric_dtype(alloc_df[col])
            }

            info_df = fetch_info(code, start_date, end_date)
            if not info_df.empty:
                info_rows[code] = info_df.iloc[-1]
        except TefasError as exc:
            errors.append(f"{code}: {exc}")

for err in errors:
    st.warning(err)

if len(allocations) < 2:
    st.error("En az iki fon için veri alınamadı, karşılaştırma yapılamıyor.")
    st.stop()

valid_codes = list(allocations.keys())

# --- KPI kartları -----------------------------------------------------
if info_rows:
    cols = st.columns(len(valid_codes))
    for i, code in enumerate(valid_codes):
        with cols[i]:
            row = info_rows.get(code)
            if row is None:
                kpi_card(code, "veri yok")
                continue
            price_col = next((c for c in row.index if "FIYAT" in c.upper()), None)
            size_col = next((c for c in row.index if "PORTFOYBUYUKLUGU" in c.upper().replace(" ", "")), None)
            value = f"{row[price_col]:.4f} TL" if price_col else "-"
            kpi_card(f"{code} · Son Fiyat", value)

st.divider()

# --- Dağılım karşılaştırma grafiği -------------------------------------
all_categories = sorted({cat for alloc in allocations.values() for cat in alloc})

fig = go.Figure()
for i, code in enumerate(valid_codes):
    alloc = allocations[code]
    fig.add_trace(
        go.Bar(
            name=code,
            x=all_categories,
            y=[alloc.get(cat, 0) for cat in all_categories],
            marker_color=fund_color(i),
        )
    )
fig.update_layout(
    **plotly_layout(
        barmode="group",
        title="Varlık Dağılımı Karşılaştırması (%)",
        yaxis_title="Portföy Yüzdesi (%)",
    )
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Fark / ortalama analizi --------------------------------------------
alloc_df = pd.DataFrame(allocations).fillna(0).T  # index: fon kodu, columns: kategori
alloc_df = alloc_df[all_categories]

if len(valid_codes) == 2:
    st.subheader(f"{valid_codes[0]} vs {valid_codes[1]} Farkı")
    diff = alloc_df.loc[valid_codes[0]] - alloc_df.loc[valid_codes[1]]
    diff_df = diff.to_frame(name="Fark (puan)").sort_values("Fark (puan)", ascending=False)
    st.dataframe(
        diff_df.style.format("{:+.2f}").background_gradient(
            cmap="RdYlGn", vmin=-diff.abs().max(), vmax=diff.abs().max()
        ),
        use_container_width=True,
    )
    biggest = diff.abs().idxmax()
    direction = valid_codes[0] if diff[biggest] > 0 else valid_codes[1]
    st.markdown(
        f"En büyük fark **{biggest}** kaleminde: **{direction}** diğerine göre "
        f"**{abs(diff[biggest]):.1f} puan** daha ağırlıklı."
    )
else:
    st.subheader("Ortalamadan Sapma Analizi")
    average = alloc_df.mean(axis=0)
    deviation = alloc_df.subtract(average, axis=1)
    st.caption("Her fonun, seçilen fonların ortalama dağılımına göre sapması (puan)")
    st.dataframe(
        deviation.style.format("{:+.2f}").background_gradient(
            cmap="RdYlGn", vmin=-deviation.abs().values.max(), vmax=deviation.abs().values.max()
        ),
        use_container_width=True,
    )
    for code in valid_codes:
        biggest_cat = deviation.loc[code].abs().idxmax()
        val = deviation.loc[code, biggest_cat]
        sign = "üzerinde" if val > 0 else "altında"
        st.markdown(
            f"- **{code}**: ortalamanın en çok **{biggest_cat}** kaleminde "
            f"({abs(val):.1f} puan) {sign}"
        )

with st.expander("Ham dağılım verisi"):
    st.dataframe(alloc_df.style.format("{:.2f}"), use_container_width=True)

download_excel_button(alloc_df, "fon_karsilastirma.xlsx")
