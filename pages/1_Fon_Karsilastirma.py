import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.cache import parse_kap_allocation, parse_kap_period
from ui.components import download_excel_button
from ui.theme import fund_color, inject_css, plotly_layout

st.set_page_config(page_title="Fon Karşılaştırma", page_icon="📊", layout="wide")
inject_css()

st.title("Fon Karşılaştırma")
st.caption(
    "Fonların KAP'ta yayınlanan aylık \"Portföy Dağılım Raporu\" PDF'lerini yükleyin, "
    "varlık sınıfı dağılımlarını ve aralarındaki farkı karşılaştırın"
)

with st.sidebar:
    st.subheader("Fon Raporları")
    uploaded_files = st.file_uploader(
        "KAP Portföy Dağılım Raporu (PDF)",
        type="pdf",
        accept_multiple_files=True,
        help="Fonu yöneten portföy yönetim şirketinin KAP bildirimlerinden indirilen aylık rapor",
    )
    st.caption(
        "KAP'ta bulmak için: fonun TEFAS sayfasındaki \"KAP Bilgi Sayfası\" linkine gidin, "
        "bildirimler arasından \"Portföy Dağılım Raporu\"nu indirin."
    )

if not uploaded_files:
    st.info("Karşılaştırmaya başlamak için en az iki fonun PDF raporunu yükleyin.")
    st.stop()

if len(uploaded_files) < 2:
    st.warning("Karşılaştırma için en az iki PDF gerekli.")
    st.stop()

allocations: dict[str, dict[str, float]] = {}
periods: dict[str, str | None] = {}
errors: list[str] = []

with st.spinner("PDF'ler okunuyor..."):
    for file in uploaded_files:
        label = file.name.rsplit(".", 1)[0]
        pdf_bytes = file.getvalue()
        try:
            alloc = parse_kap_allocation(pdf_bytes)
        except Exception as exc:
            errors.append(f"{label}: PDF okunamadı ({exc})")
            continue
        if not alloc or sum(alloc.values()) == 0:
            errors.append(f"{label}: dağılım verisi bulunamadı - bu rapor tanıdığımız formatta değil olabilir")
            continue
        allocations[label] = alloc
        periods[label] = parse_kap_period(pdf_bytes)

for err in errors:
    st.warning(err)

if len(allocations) < 2:
    st.error("En az iki fon için veri okunamadı, karşılaştırma yapılamıyor.")
    st.stop()

valid_labels = list(allocations.keys())

st.caption(
    "Dönem: "
    + " · ".join(f"**{lbl}**: {periods.get(lbl) or 'bilinmiyor'}" for lbl in valid_labels)
)

st.divider()

# --- Dağılım karşılaştırma grafiği -------------------------------------
all_categories = sorted({cat for alloc in allocations.values() for cat in alloc if alloc[cat] > 0})

fig = go.Figure()
for i, label in enumerate(valid_labels):
    alloc = allocations[label]
    fig.add_trace(
        go.Bar(
            name=label,
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
alloc_df = pd.DataFrame(allocations).fillna(0).T  # index: fon, columns: kategori
alloc_df = alloc_df[all_categories] if all_categories else alloc_df

if len(valid_labels) == 2:
    st.subheader(f"{valid_labels[0]} vs {valid_labels[1]} Farkı")
    diff = alloc_df.loc[valid_labels[0]] - alloc_df.loc[valid_labels[1]]
    diff_df = diff.to_frame(name="Fark (puan)").sort_values("Fark (puan)", ascending=False)
    st.dataframe(
        diff_df.style.format("{:+.2f}").background_gradient(
            cmap="RdYlGn", vmin=-diff.abs().max(), vmax=diff.abs().max()
        ),
        use_container_width=True,
    )
    biggest = diff.abs().idxmax()
    direction = valid_labels[0] if diff[biggest] > 0 else valid_labels[1]
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
    for label in valid_labels:
        biggest_cat = deviation.loc[label].abs().idxmax()
        val = deviation.loc[label, biggest_cat]
        sign = "üzerinde" if val > 0 else "altında"
        st.markdown(
            f"- **{label}**: ortalamanın en çok **{biggest_cat}** kaleminde "
            f"({abs(val):.1f} puan) {sign}"
        )

with st.expander("Ham dağılım verisi"):
    st.dataframe(alloc_df.style.format("{:.2f}"), use_container_width=True)

download_excel_button(alloc_df, "fon_karsilastirma.xlsx")
