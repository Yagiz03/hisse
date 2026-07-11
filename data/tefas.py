"""TEFAS (Türkiye Elektronik Fon Alım Satım Platformu) veri istemcisi.

Resmi bir API dokümantasyonu yok; burada kullanılan uç noktalar TEFAS'ın kendi
web sitesinin (tefas.gov.tr) arka planda çağırdığı, topluluk tarafından ters
mühendislikle tespit edilmiş uç noktalardır. TEFAS zaman zaman bu uç noktaları
değiştirebilir - hata alınırsa önce tarayıcıda tefas.gov.tr üzerinde Ağ (Network)
sekmesinden güncel istek/yanıt şeklini doğrulamak gerekir.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import requests

BASE_URL = "https://www.tefas.gov.tr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/TarihselVeriler.aspx",
}

# TEFAS dağılım tablosundaki varlık sınıfı kolonlarının makine adı -> ekranda
# gösterilecek Türkçe etiket eşlemesi. Gerçek API yanıtı doğrulandığında
# eksik/yanlış kolon adları burada düzeltilmeli.
ALLOCATION_COLUMNS = {
    "hisse": "Hisse Senedi",
    "kamu": "Kamu Borçlanma Araçları",
    "ozelsektortahvil": "Özel Sektör Tahvili",
    "ters": "Ters Repo",
    "takasbank": "Takasbank Para Piyasası",
    "yabancimenkul": "Yabancı Menkul Kıymet",
    "altin": "Altın / Kıymetli Maden",
    "diger": "Diğer",
}


class TefasError(RuntimeError):
    """TEFAS'tan beklenmeyen/işlenemeyen bir yanıt geldiğinde fırlatılır."""


class TefasClient:
    def __init__(self, timeout: int = 15):
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._timeout = timeout

    def _post(self, endpoint: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{BASE_URL}/api/DB/{endpoint}"
        try:
            resp = self._session.post(url, data=payload, timeout=self._timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise TefasError(f"{endpoint} isteği başarısız: {exc}") from exc

        try:
            body = resp.json()
        except ValueError as exc:
            raise TefasError(f"{endpoint} JSON olmayan yanıt döndürdü") from exc

        rows = body.get("data") if isinstance(body, dict) else body
        if rows is None:
            raise TefasError(f"{endpoint} yanıtında beklenen 'data' alanı yok: {body!r}")
        return rows

    def get_fund_allocation(
        self, fund_code: str, start_date: date, end_date: date, fund_type: str = "YAT"
    ) -> pd.DataFrame:
        """Bir fonun tarih aralığındaki varlık dağılımı yüzdelerini döndürür."""
        payload = {
            "fontip": fund_type,
            "fonkod": fund_code,
            "bastarih": start_date.strftime("%d.%m.%Y"),
            "bittarih": end_date.strftime("%d.%m.%Y"),
        }
        rows = self._post("BindHistoryAllocation", payload)
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        if "TARIH" in df.columns:
            df["TARIH"] = pd.to_datetime(df["TARIH"], unit="ms", errors="coerce")
            df = df.sort_values("TARIH")
        return df

    def get_fund_info(
        self, fund_code: str, start_date: date, end_date: date, fund_type: str = "YAT"
    ) -> pd.DataFrame:
        """Fiyat, toplam değer, yatırımcı sayısı gibi genel fon bilgilerini döndürür."""
        payload = {
            "fontip": fund_type,
            "fonkod": fund_code,
            "bastarih": start_date.strftime("%d.%m.%Y"),
            "bittarih": end_date.strftime("%d.%m.%Y"),
        }
        rows = self._post("BindHistoryInfo", payload)
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        if "TARIH" in df.columns:
            df["TARIH"] = pd.to_datetime(df["TARIH"], unit="ms", errors="coerce")
            df = df.sort_values("TARIH")
        return df

    def latest_allocation(
        self, fund_code: str, start_date: date, end_date: date, fund_type: str = "YAT"
    ) -> dict[str, float]:
        """Aralıktaki en güncel satırdan varlık dağılımı yüzdelerini çıkarır."""
        df = self.get_fund_allocation(fund_code, start_date, end_date, fund_type)
        if df.empty:
            raise TefasError(f"{fund_code} için dağılım verisi bulunamadı")
        last_row = df.iloc[-1]
        result = {}
        for key, label in ALLOCATION_COLUMNS.items():
            for col in df.columns:
                if col.lower() == key:
                    result[label] = float(last_row[col] or 0)
                    break
        return result
