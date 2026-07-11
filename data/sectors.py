"""BIST30 şirketleri için statik sektör eşlemesi.

İş Yatırım API'sinde sektör alanı yok; bu yüzden sektör ısı haritası için
elle tutulan bir eşleme kullanıyoruz. Kapsam şimdilik BIST30 ile sınırlı -
BIST100'e genişletmek istersek bu sözlüğü büyütmek yeterli, kod tarafında
değişiklik gerekmez. Zaman zaman şirketlerin endeks/sektör durumu değişebilir,
periyodik gözden geçirme gerekir.
"""

BIST30_SECTORS: dict[str, str] = {
    "AKBNK": "Bankacılık",
    "GARAN": "Bankacılık",
    "ISCTR": "Bankacılık",
    "YKBNK": "Bankacılık",
    "VAKBN": "Bankacılık",
    "HALKB": "Bankacılık",
    "SAHOL": "Holding",
    "KCHOL": "Holding",
    "ALARK": "Holding",
    "SISE": "Cam / Sanayi",
    "EREGL": "Demir-Çelik",
    "KRDMD": "Demir-Çelik",
    "TUPRS": "Enerji / Rafineri",
    "PETKM": "Petrokimya",
    "ASELS": "Savunma Sanayi",
    "THYAO": "Ulaştırma",
    "PGSUS": "Ulaştırma",
    "TCELL": "Telekomünikasyon",
    "TTKOM": "Telekomünikasyon",
    "BIMAS": "Perakende",
    "MGROS": "Perakende",
    "FROTO": "Otomotiv",
    "TOASO": "Otomotiv",
    "OTKAR": "Otomotiv",
    "ARCLK": "Dayanıklı Tüketim",
    "TAVHL": "Havacılık / Altyapı",
    "ENKAI": "İnşaat / Taahhüt",
    "KOZAL": "Madencilik",
    "KOZAA": "Madencilik",
    "SASA": "Kimya",
}
