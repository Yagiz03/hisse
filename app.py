import streamlit as st

from ui.nav import top_nav
from ui.theme import inject_css

st.set_page_config(
    page_title="Hisse Masası",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
top_nav("Ana Sayfa")

st.title("Hisse Masası")
st.caption("Portföy yönetimi için fon karşılaştırma ve piyasa analiz paneli")

st.divider()

MODULES = [
    {
        "title": "Fon Karşılaştırma",
        "desc": "KAP'taki fon raporlarından varlık dağılımını yan yana karşılaştırın, risk profillerini görün.",
        "icon": "📊",
        "path": "pages/1_Fon_Karsilastirma.py",
    },
    {
        "title": "Finansal Tablolar",
        "desc": "BIST şirketlerinin bilanço / gelir tablosu kalemlerini, rasyolarını ve tam finansal tablolarını inceleyin.",
        "icon": "📈",
        "path": "pages/2_Finansal_Tablolar.py",
    },
    {
        "title": "Sektör Isı Haritası",
        "desc": "BIST30'un sektör bazlı performansını, en çok yükselen/düşenleri tek bakışta görün.",
        "icon": "🗺️",
        "path": "pages/3_Sektor_Isi_Haritasi.py",
    },
    {
        "title": "Portföy Simülasyonu",
        "desc": "Ağırlıklı bir portföyün geçmiş performansını XU100'e karşı test edin, riskini ölçün.",
        "icon": "💼",
        "path": "pages/4_Portfoy_Simulasyonu.py",
    },
]

cols = st.columns(2)
for i, module in enumerate(MODULES):
    with cols[i % 2]:
        st.markdown(
            f"""
            <div class="kpi-card" style="min-height: 130px;">
                <div style="font-size: 1.6rem;">{module['icon']}</div>
                <div class="kpi-value" style="font-size: 1.15rem; margin-top: 6px;">{module['title']}</div>
                <div class="kpi-label" style="text-transform: none; letter-spacing: normal; margin-top: 6px; line-height: 1.4;">
                    {module['desc']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(module["path"], label=f"{module['title']}'a git →", icon=None)
