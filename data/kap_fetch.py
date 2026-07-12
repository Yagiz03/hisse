"""KAP'tan fon kodu ile otomatik "Portföy Dağılım Raporu" PDF çekimi.

Akış (tarayıcı Network sekmesinden ters mühendislikle bulundu):

1. POST /tr/api/search/combined {"keyword": <fon kodu>, ...} -> memberOrFundOid
2. GET /tr/fon-bilgileri/ozet/<memberOrFundOid>  -> sayfa HTML'inde en güncel
   "Portföy Dağılım Raporu" PDF'inin indirme linki (api/file/download/<id>) geçiyor
3. GET /tr/api/file/download/<id> -> PDF baytları

KAP, bilinen bot koruması (Akamai benzeri) kullanıyor; bu yüzden bu akış
tarayıcıda çalışsa da sunucudan (örn. Streamlit Cloud) her zaman çalışacağının
garantisi yok. Böyle bir durumda kullanıcı manuel PDF yüklemeye geri düşebilir
(bkz. pages/1_Fon_Karsilastirma.py).
"""

from __future__ import annotations

import re

import requests

BASE_URL = "https://www.kap.org.tr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr",
}

FILE_LINK_RE = re.compile(r"api/file/download/([a-f0-9]{32})")


class KapFetchError(RuntimeError):
    pass


class KapAutoFetcher:
    def __init__(self, timeout: int = 8):
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._timeout = timeout
        try:
            self._session.get(BASE_URL, timeout=timeout)
        except requests.RequestException:
            pass  # sadece çerez almak için deneniyor, başarısız olursa devam edilir

    def find_fund_oid(self, fund_code: str) -> str:
        try:
            resp = self._session.post(
                f"{BASE_URL}/tr/api/search/combined",
                json={"keyword": fund_code, "discClass": "ALL", "lang": "tr", "channel": "WEB"},
                headers={
                    "Content-Type": "application/json",
                    "Origin": BASE_URL,
                    "Referer": f"{BASE_URL}/tr",
                },
                timeout=self._timeout,
            )
            resp.raise_for_status()
            categories = resp.json()
        except requests.RequestException as exc:
            raise KapFetchError(f"KAP arama isteği başarısız ({exc})") from exc
        except ValueError as exc:
            raise KapFetchError(f"KAP arama yanıtı beklenmeyen formatta ({exc})") from exc

        for cat in categories:
            if cat.get("category") != "companyOrFunds":
                continue
            for result in cat.get("results", []):
                if result.get("cmpOrFundCode", "").upper() == fund_code.upper():
                    return result["memberOrFundOid"]
        raise KapFetchError(f"KAP aramasında '{fund_code}' fon kodu bulunamadı")

    def find_latest_report_url(self, fund_oid: str) -> str:
        try:
            resp = self._session.get(
                f"{BASE_URL}/tr/fon-bilgileri/ozet/{fund_oid}",
                headers={"Referer": f"{BASE_URL}/tr"},
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise KapFetchError(f"Fon özet sayfası alınamadı ({exc})") from exc

        text = resp.text
        matches = list(FILE_LINK_RE.finditer(text))
        if not matches:
            raise KapFetchError(
                f"Fon özet sayfasında (oid={fund_oid}) Portföy Dağılım Raporu linki bulunamadı"
            )

        # Özet sayfasında izahname, fon bilgilendirme formu gibi başka
        # bildirim linkleri de geçiyor - körü körüne İLK linki almak yanlış
        # PDF'i indirip "tanımadığımız format" hatasına yol açıyordu. Önce,
        # metinde hemen öncesinde "Portföy Dağılım" ifadesi geçen linki ara;
        # bulunamazsa (sayfa yapısı beklenenden farklıysa) son çare olarak
        # ilk linke düş.
        best = None
        for m in matches:
            window = text[max(0, m.start() - 400) : m.start()]
            if re.search(r"PORTF[ÖO]Y\s*DA[ĞG]ILIM", window, re.IGNORECASE):
                best = m
                break
        match = best or matches[0]
        return f"{BASE_URL}/tr/api/file/download/{match.group(1)}"

    def download_pdf(self, url: str) -> bytes:
        try:
            resp = self._session.get(url, headers={"Referer": BASE_URL}, timeout=self._timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise KapFetchError(f"PDF indirilemedi ({exc})") from exc

        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and not resp.content.startswith(b"%PDF"):
            raise KapFetchError(f"İndirilen dosya PDF değil (Content-Type: {content_type})")
        return resp.content

    def fetch_latest_allocation_pdf(self, fund_code: str) -> bytes:
        oid = self.find_fund_oid(fund_code)
        pdf_url = self.find_latest_report_url(oid)
        return self.download_pdf(pdf_url)
