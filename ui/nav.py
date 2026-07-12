"""Üst yatay navigasyon çubuğu.

Streamlit'in varsayılan sidebar sayfa listesi `inject_css` içinde gizleniyor;
onun yerine her sayfanın en üstünde bu pill-tab menüyü gösteriyoruz.
"""

import streamlit as st
from streamlit_option_menu import option_menu

from ui.theme import CATEGORICAL, SURFACE, TEXT_MUTED, TEXT_PRIMARY

PAGES = [
    {"label": "Ana Sayfa", "icon": "house", "path": "app.py"},
    {"label": "Fon Karşılaştırma", "icon": "pie-chart", "path": "pages/1_Fon_Karsilastirma.py"},
    {"label": "Finansal Tablolar", "icon": "table", "path": "pages/2_Finansal_Tablolar.py"},
    {"label": "Sektör Isı Haritası", "icon": "grid-3x3", "path": "pages/3_Sektor_Isi_Haritasi.py"},
    {"label": "Portföy Simülasyonu", "icon": "briefcase", "path": "pages/4_Portfoy_Simulasyonu.py"},
]


def top_nav(active_label: str) -> None:
    labels = [p["label"] for p in PAGES]
    icons = [p["icon"] for p in PAGES]

    selected = option_menu(
        menu_title=None,
        options=labels,
        icons=icons,
        default_index=labels.index(active_label),
        orientation="horizontal",
        styles={
            "container": {
                "padding": "6px",
                "background-color": SURFACE,
                "border-radius": "12px",
                "border": "1px solid rgba(255,255,255,0.08)",
                "margin-bottom": "24px",
            },
            "icon": {"font-size": "14px"},
            "nav-link": {
                "font-size": "14px",
                "color": TEXT_MUTED,
                "text-align": "center",
                "margin": "2px",
                "border-radius": "8px",
                "padding": "10px 18px",
                "--hover-color": "rgba(255,255,255,0.06)",
            },
            "nav-link-selected": {
                "background": f"linear-gradient(90deg, {CATEGORICAL[0]}, {CATEGORICAL[4]})",
                "color": TEXT_PRIMARY,
                "font-weight": "600",
                "box-shadow": "none",
            },
        },
        key=f"top_nav_{active_label}",
    )

    if selected != active_label:
        target = next(p["path"] for p in PAGES if p["label"] == selected)
        st.switch_page(target)
