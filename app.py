import streamlit as st

from ui.theme import inject_css

st.set_page_config(
    page_title="Hisse Masası",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

pages = [
    st.Page("pages/1_Fon_Karsilastirma.py", title="Fon Karşılaştırma", icon=":material/pie_chart:", default=True),
    st.Page("pages/2_Finansal_Tablolar.py", title="Finansal Tablolar", icon=":material/table_chart:"),
    st.Page("pages/3_Sektor_Isi_Haritasi.py", title="Sektör Isı Haritası", icon=":material/grid_view:"),
    st.Page("pages/4_Portfoy_Simulasyonu.py", title="Portföy Simülasyonu", icon=":material/work:"),
]

pg = st.navigation(pages, position="top")
pg.run()
