from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.cache import fetch_kap_allocation_pdf, parse_kap_allocation, parse_kap_holdings, parse_kap_period
from data.kap_fetch import KapFetchError
from ui.components import download_excel_button, kpi_card
from ui.nav import top_nav
from ui.theme import fund_color, inject_css, plotly_layout

st.set_page_config(page_title="Fon Karşılaştırma", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")
inject_css()
top_nav("Fon Karşılaştırma")

st.title("Fon Karşılaştırma")
st.caption(
    "Fonların KAP'ta yayınlanan aylık \"Portföy Dağılım Raporu\" verilerini karşılaştırın"
)

with st.container(border=True):
    st.subheader("Fon Raporları")
    mode = st.radio(
        "Kaynak",
        ["Fon kodu ile otomatik getir", "PDF yükle"],
        help="Otomatik getirme KAP'ın bot korumasına takılırsa PDF yükleme yöntemine geç",
        horizontal=True,
    )

    auto_codes: list[str] = []
    uploaded_files = []
    if mode == "Fon kodu ile otomatik getir":
        codes_input = st.text_input("Fon kodları (virgülle ayırın)", placeholder="Örn: BHL, AK3, BID")
        auto_codes = [c.strip().upper() for c in codes_input.split(",") if c.strip()]
    else:
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

has_input = len(auto_codes) >= 2 or len(uploaded_files) >= 2
if not has_input:
    st.info("Karşılaştırmaya başlamak için en az iki fon girin.")
    st.stop()

allocations: dict[str, dict[str, float]] = {}
periods: dict[str, str | None] = {}
pdf_bytes_by_label: dict[str, bytes] = {}
errors: list[str] = []

with st.spinner("Fon raporları alınıyor..."):
    if auto_codes:
        with ThreadPoolExecutor(max_workers=min(len(auto_codes), 6)) as pool:
            futures = {pool.submit(fetch_kap_allocation_pdf, code): code for code in auto_codes}
            for future in as_completed(futures):
                code = futures[future]
                try:
                    pdf_bytes = future.result()
                except KapFetchError as exc:
                    errors.append(f"{code}: KAP'tan alınamadı ({exc})")
                    continue
                except Exception as exc:
                    errors.append(f"{code}: KAP'tan alınamadı, beklenmeyen hata ({exc})")
                    continue
                alloc = parse_kap_allocation(pdf_bytes)
                if not alloc or sum(alloc.values()) == 0:
                    errors.append(f"{code}: dağılım verisi bulunamadı - rapor tanıdığımız formatta değil olabilir")
                    continue
                allocations[code] = alloc
                periods[code] = parse_kap_period(pdf_bytes)
                pdf_bytes_by_label[code] = pdf_bytes
    else:
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
            pdf_bytes_by_label[label] = pdf_bytes

for err in errors:
    st.warning(err)

if auto_codes and errors:
    st.caption(
        "Otomatik getirme başarısız olursa KAP'ın bot koruması engelliyor olabilir - "
        "soldaki menüden \"PDF yükle\" seçeneğine geçip raporu manuel indirip yükleyebilirsin."
    )

if len(allocations) < 2:
    st.error("En az iki fon için veri okunamadı, karşılaştırma yapılamıyor.")
    st.stop()

ordered_labels = auto_codes if auto_codes else [f.name.rsplit(".", 1)[0] for f in uploaded_files]
valid_labels = [lbl for lbl in ordered_labels if lbl in allocations]

st.caption(
    "Dönem: "
    + " · ".join(f"**{lbl}**: {periods.get(lbl) or 'bilinmiyor'}" for lbl in valid_labels)
)

st.divider()


def _risk_tier(hisse_pct: float) -> tuple[str, bool | None]:
    if hisse_pct >= 75:
        return "Yüksek Risk", False
    if hisse_pct >= 30:
        return "Orta Risk", None
    return "Düşük Risk", True


cols = st.columns(len(valid_labels))
for i, label in enumerate(valid_labels):
    with cols[i]:
        hisse_pct = allocations[label].get("Hisse Senedi", 0.0)
        tier, tier_good = _risk_tier(hisse_pct)
        kpi_card(f"{label} · Risk Profili", tier, delta=f"Hisse Senedi %{hisse_pct:.0f}", delta_good=tier_good)

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

# --- Hisse bazlı en büyük pozisyonlar --------------------------------------
holdings_by_label: dict[str, pd.DataFrame] = {}
for label in valid_labels:
    pdf_bytes = pdf_bytes_by_label.get(label)
    if pdf_bytes is None:
        continue
    h = parse_kap_holdings(pdf_bytes)
    if not h.empty:
        holdings_by_label[label] = h.groupby("kod", as_index=False)["agirlik_pct"].sum()

if holdings_by_label:
    st.divider()
    st.subheader("En Büyük Pozisyonlar (Hisse Bazlı)")
    st.caption(
        "Raporun 'Fon Portföy Değeri Tablosu' bölümünden çıkarıldı - bazı fonlarda toplamlar "
        "resmi Hisse Senedi yüzdesinden birkaç puan sapabilir (rapor formatına bağlı), "
        "bu yüzden gösterge niteliğindedir; kesin karar için PDF'in kendisine bakın."
    )
    cols = st.columns(len(holdings_by_label))
    for i, (label, h) in enumerate(holdings_by_label.items()):
        with cols[i]:
            st.markdown(f"**{label}**")
            top10 = h.sort_values("agirlik_pct", ascending=False).head(10).set_index("kod")
            st.dataframe(top10.rename(columns={"agirlik_pct": "Ağırlık (%)"}).style.format("{:.2f}"), use_container_width=True)

    if len(holdings_by_label) >= 2:
        common = set.intersection(*[set(h["kod"]) for h in holdings_by_label.values()])
        if common:
            st.markdown(f"**Ortak taşınan hisseler ({len(common)}):** " + ", ".join(sorted(common)))
        else:
            st.caption("Seçilen fonların ortak taşıdığı hisse bulunamadı.")
