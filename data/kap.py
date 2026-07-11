"""KAP (Kamuyu Aydınlatma Platformu) yedek veri kaynağı.

İş Yatırım'dan (`data/financials.py`) bir kalem çekilemediğinde buraya
düşülmesi planlanıyor. KAP finansal tabloları XBRL/Excel formatında yayınlar
ve şirket/dönem bazlı doküman keşfi + XBRL ayrıştırma gerektirir; bu, İş
Yatırım entegrasyonundan bağımsız, kendi başına bir iş parçası olduğu için
şimdilik somut bir eksik kalem/şirket örneğiyle karşılaşınca ele alınacak.

Bu modül, o zaman dolduracağımız arayüzü şimdiden sabitliyor.
"""

from __future__ import annotations


class KapNotImplementedError(NotImplementedError):
    pass


def fetch_financial_item(symbol: str, item: str, year: int, period: int) -> float:
    raise KapNotImplementedError(
        f"KAP fallback henüz uygulanmadı ({symbol} / {item} / {year}-{period}). "
        "İş Yatırım'da bulunamayan somut bir kalemle karşılaşınca bu fonksiyonu "
        "KAP'ın XBRL doküman servisine göre dolduracağız."
    )
