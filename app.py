import streamlit as st

from ui.theme import inject_css

st.set_page_config(
    page_title="Hisse Masası",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

st.title("Hisse Masası")
st.caption("Portföy yönetimi için fon karşılaştırma ve piyasa analiz paneli")

st.markdown(
    """
    Soldaki menüden bir modül seçin:

    - **Fon Karşılaştırma** — TEFAS fonlarının varlık dağılımını yan yana karşılaştırın
    """
)
