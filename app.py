from datetime import datetime

import streamlit as st

from ui.theme import inject_css

st.set_page_config(
    page_title="Hisse Masası",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# Fiyat/finansal veri 6 saat, KAP fon raporları 24 saat önbellekleniyor
# (bkz. data/cache.py) - kullanıcı TTL dolmadan tazelemek isterse diye
# üst çubuğa manuel bir "veriyi yenile" kontrolü ekliyoruz.
with st.container(key="veri_yenile_bar"):
    with st.popover("↻ Veriyi yenile", help="Önbelleklenmiş fiyat/finansal/fon verisini temizleyip yeniden çeker"):
        if "_son_yenileme" in st.session_state:
            st.caption(f"Son yenileme: {st.session_state['_son_yenileme']}")
        if st.button("Önbelleği temizle ve yenile"):
            st.cache_data.clear()
            st.session_state["_son_yenileme"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            st.rerun()

pages = [
    st.Page("pages/1_Fon_Karsilastirma.py", title="Fon Karşılaştırma", icon=":material/pie_chart:", default=True),
    st.Page("pages/2_Finansal_Tablolar.py", title="Finansal Tablolar", icon=":material/table_chart:"),
    st.Page("pages/3_Sektor_Isi_Haritasi.py", title="Sektör Isı Haritası", icon=":material/grid_view:"),
    st.Page("pages/4_Portfoy_Simulasyonu.py", title="Portföy Simülasyonu", icon=":material/work:"),
]

pg = st.navigation(pages, position="top")
pg.run()
