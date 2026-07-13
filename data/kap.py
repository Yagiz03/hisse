"""KAP (Kamuyu Aydınlatma Platformu) "Portföy Dağılım Raporu" PDF ayrıştırıcısı.

SPK'nın zorunlu kıldığı aylık fon bildirim formu, tüm portföy yönetim
şirketlerinde aynı veri alanlarını içerir ("Aylık Ortalama Portföydeki
Menkul Kıymetler Yüzdesi" ve tek tek varlık satırları) ama görsel yerleşim
şirketten şirkete değişir. Bu yüzden sabit X/Y koordinatına değil, aynı
satırdaki metin parçalarını Y-koordinatına göre gruplayıp solda etiket
sağda değeri eşleştiren bir yönteme dayanıyoruz - iki farklı biçimi de
(harfli liste / düz liste) kapsayacak şekilde.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Union

import fitz
import pandas as pd

PdfSource = Union[str, bytes]


def _open(pdf: PdfSource) -> fitz.Document:
    if isinstance(pdf, (bytes, bytearray)):
        return fitz.open(stream=pdf, filetype="pdf")
    return fitz.open(pdf)


_ROW_TOLERANCE = 2.0

_ALLOCATION_PAGE_ANCHOR = re.compile(r"MENKUL\s*KIYMETLER\s*Y[ÜU]ZDES[İI]", re.IGNORECASE)
_ALLOCATION_ROW_TRIGGER = re.compile(r"Y[ÜU]ZDES[İI]", re.IGNORECASE)
_HOLDINGS_ANCHOR = re.compile(r"FON\s*PORTF[ÖO]Y\s*DE[ĞG]ER[İI]\s*TABLOSU", re.IGNORECASE)
# Yeni bir üst seviye alan başlığı (örn. "G-)..." ya da "F. ...") - küçük harfli
# alt kalemlerden (a-, b-, g2- gibi) ayırmak için büyük/küçük harf duyarlı.
_TOP_LEVEL_HEADER = re.compile(r"^[A-ZÇĞİÖŞÜ]\.(\s|$)|^[A-ZÇĞİÖŞÜ]-\)|^(IV|V|III|II)[-\s]")
_LABEL_PREFIX = re.compile(r"^[a-zçğıöşüA-ZÇĞİÖŞÜ]\d?[\.\-]\)?\s*")
_NUMBER = re.compile(r"-?\d[\d.,]*\s*%?$")

# Görülen tüm etiket varyasyonlarını standart bir isme indiren eşleme.
CANONICAL_LABELS = {
    "HİSSE SENEDİ": "Hisse Senedi",
    "HAZİNE BONOSU": "Hazine Bonosu",
    "DEVLET TAHVİLİ": "Devlet Tahvili",
    "ÖZEL SEKTÖR TAHVİLİ": "Özel Sektör Tahvili",
    "KİRA SERTİFİKALARI": "Kira Sertifikaları",
    "FİNANSMAN BONUSU": "Finansman Bonosu",
    "TPP-TPP BORÇLANMA": "TPP Borçlanma",
    "BPP-BPP BORÇLANMA": "BPP Borçlanma",
    "OPSİYON": "Opsiyon",
    "VARANT": "Varant",
    "DEĞERLİ MADEN": "Değerli Maden",
    "MEVDUAT": "Mevduat",
    "KATILIM HESABI": "Katılım Hesabı",
    "DİĞER": "Diğer",
    "TEMİNAT": "Teminat",
    "YATIRIM FONU": "Yatırım Fonu",
    "YATIRIM FONU KATILMA PAYI": "Yatırım Fonu",
    "BORSA YATIRIM FONU": "Borsa Yatırım Fonu",
    "REPO-TREPO": "Repo",
    "TAKASBANK PARA PİYASASI": "Takasbank Para Piyasası",
    "TAAHHÜTLÜ ALIŞ-SATIŞ İŞLEMLERİ": "Taahhütlü Alış-Satış",
    "VAAD SÖZLEŞMESİ İŞLEMLERİ": "Vaad Sözleşmesi",
}


@dataclass
class Span:
    y: float
    x: float
    text: str


def _page_rows(page: fitz.Page) -> list[list[Span]]:
    spans: list[Span] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if text:
                    spans.append(Span(round(span["bbox"][1], 1), round(span["bbox"][0], 1), text))
    spans.sort(key=lambda s: (s.y, s.x))

    rows: list[list[Span]] = []
    for span in spans:
        if rows and abs(rows[-1][0].y - span.y) <= _ROW_TOLERANCE:
            rows[-1].append(span)
        else:
            rows.append([span])
    for row in rows:
        row.sort(key=lambda s: s.x)
    return rows


_TR_FOLD_MAP = str.maketrans({"i": "I", "İ": "I", "ı": "I", "I": "I"})


def _fold_tr(text: str) -> str:
    """i/İ/ı/I harflerini karşılaştırma için tek bir forma indirger.

    Python'un varsayılan `str.upper()`/`.title()` yerelden bağımsızdır ve
    Türkçe noktalı/noktasız i çiftini doğru çeviremez (örn. "Kira" ->
    "KIRA" olur, "KİRA" olması gerekirken). Üstüne üstlük kaynak PDF'ler
    de tutarsız: "ı" sesi çoğu zaman düz ASCII "i" ile yazılmış oluyor
    (örn. "Katilim Hesabı"). Bu yüzden tek yönlü bir büyük harfe çevirme
    yerine, eşleştirme için dört harfi de aynı sembole indirgeyip
    karşılaştırıyoruz; ekranda gösterilecek doğru yazım zaten
    CANONICAL_LABELS sözlüğünde hazır duruyor.
    """
    return text.translate(_TR_FOLD_MAP).upper()


_CANONICAL_LOOKUP = {_fold_tr(k): v for k, v in CANONICAL_LABELS.items()}


def _canonical(label: str) -> str:
    key = _LABEL_PREFIX.sub("", label).strip()
    key = re.sub(r"\s+", " ", key)
    found = _CANONICAL_LOOKUP.get(_fold_tr(key))
    return found if found is not None else key.title()


def _find_anchor_page(doc: fitz.Document, pattern: re.Pattern, max_pages: int = 5) -> int | None:
    for i in range(min(max_pages, len(doc))):
        if pattern.search(doc[i].get_text()):
            return i
    return None


def _parse_allocation_from_page(page: fitz.Page) -> dict[str, float]:
    rows = _page_rows(page)
    started = False
    result: dict[str, float] = {}

    for row in rows:
        line = " ".join(s.text for s in row)
        if not started:
            if _ALLOCATION_ROW_TRIGGER.search(line):
                started = True
            continue
        if _TOP_LEVEL_HEADER.match(row[0].text.strip()):
            break

        label_parts = [s.text for s in row if not _NUMBER.match(s.text) and s.text != ":"]
        value_parts = [s.text for s in row if _NUMBER.match(s.text)]
        if not label_parts or not value_parts:
            continue

        label = _canonical(" ".join(label_parts))
        raw_value = value_parts[-1].replace("%", "").strip()
        raw_value = raw_value.replace(".", "").replace(",", ".") if "," in raw_value else raw_value
        try:
            pct = float(raw_value)
        except ValueError:
            continue
        result[label] = pct

    return result


def _label_to_canonical(label: str) -> str | None:
    """Bir satır etiketini bilinen (SPK standart) varlık sınıfı adına eşler.

    Tam eşleşme yoksa alt-dize eşleşmesi de dener (rapor formatına göre
    etiketler kısaltılmış/genişletilmiş olabilir, örn. "HİSSE SENEDİ (%)"
    ya da "B) HİSSE SENEDİ").
    """
    canon = _canonical(label)
    if canon in CANONICAL_LABELS.values():
        return canon
    folded = _fold_tr(re.sub(r"\s+", " ", label).strip())
    for key, val in CANONICAL_LABELS.items():
        if _fold_tr(key) in folded:
            return val
    return None


def _parse_allocation_fallback(doc: fitz.Document, max_pages: int = 60) -> dict[str, float]:
    """Bilinen "anchor" ifadesi (`MENKUL KIYMETLER YÜZDESİ` vb.) bulunamadığında
    ya da bulunan sayfa boş/anlamsız sonuç verdiğinde kullanılan son çare:
    sayfa başlığı aramaksızın, satırları doğrudan bilinen varlık sınıfı
    etiketleriyle eşleştirmeye çalışır. Rapor düzeni tamamen farklı olsa bile
    (farklı portföy yönetim şirketi şablonu, beklenmeyen bir doküman vb.)
    satırlar "ETİKET ... YÜZDE" şeklindeyse veri çıkarabilir.
    """
    result: dict[str, float] = {}
    for pno in range(min(max_pages, len(doc))):
        rows = _page_rows(doc[pno])
        for row in rows:
            label_parts = [s.text for s in row if not _NUMBER.match(s.text) and s.text != ":"]
            value_parts = [s.text for s in row if _NUMBER.match(s.text)]
            if not label_parts or not value_parts:
                continue
            canon = _label_to_canonical(" ".join(label_parts))
            if canon is None or canon in result:
                continue
            raw_value = value_parts[-1].replace("%", "").strip()
            raw_value = raw_value.replace(".", "").replace(",", ".") if "," in raw_value else raw_value
            try:
                pct = float(raw_value)
            except ValueError:
                continue
            if 0 <= pct <= 100:
                result[canon] = pct
    return result


def parse_allocation(pdf: PdfSource) -> dict[str, float]:
    """Fonun varlık sınıfı bazlı yüzdelik dağılımını döndürür (etiket -> yüzde)."""
    doc = _open(pdf)
    page_no = _find_anchor_page(doc, _ALLOCATION_PAGE_ANCHOR, max_pages=min(30, len(doc)))
    result = _parse_allocation_from_page(doc[page_no]) if page_no is not None else {}

    total = sum(result.values())
    if not result or not (90 <= total <= 110):
        fallback = _parse_allocation_fallback(doc)
        if sum(fallback.values()) > total:
            result = fallback

    return result


_NON_INSTRUMENT_CODES = {"GRUP", "TOPLAM", "ISIN"}
_NEW_SECTION_ROW = re.compile(r"^(IV|V|VI|VII|VIII|IX)[-\s]")


def _weight_column_x(rows: list[list[Span]]) -> tuple[float, bool] | None:
    """Fonun TOPLAM DEĞERİNE göre ağırlık sütununun X konumunu bulur.

    "GRUP (%)" sütunu yanıltıcı: bir kalemin sadece kendi alt grubu içindeki
    payını gösterir (örn. sadece hisse senetleri arasındaki pay), fonun
    tamamına göre değil. "TOPLAM (FTD GÖRE)" sütunu ise gerçek "fonun toplam
    değerine göre ağırlık" - gerçek pozisyon büyüklükleriyle çapraz kontrol
    edilerek doğrulandı. Bu yüzden önce "FTD" arıyoruz.

    Sadece tek bir düz "%" sütunu olan (FTD içermeyen) daha basit raporlarda
    bu sütun da genelde sadece görüntülenen alt tablonun (örn. yalnızca
    hisse senetleri) kendi toplamına göredir - bunu ikinci elemanla
    (`is_section_relative=True`) işaretliyoruz ki çağıran taraf fonun genel
    varlık sınıfı yüzdesiyle ölçekleyebilsin.
    """
    for row in rows:
        for span in row:
            if "FTD" in span.text.upper():
                return span.x, False
    for row in rows:
        for span in row:
            if span.text.strip() in ("%", "(%)"):
                return span.x, True
    return None


def parse_holdings(pdf: PdfSource) -> pd.DataFrame:
    """Fonun tek tek taşıdığı menkul kıymetleri ve fon içi ağırlıklarını döndürür.

    Şirketten şirkete tablo sütun sayısı/sırası değiştiği için değer sütununu
    konumundan (en sağdaki sayı) değil, başlıkta bulunan doğru yüzde sütununa
    en yakın sayıyı seçerek buluyoruz - bu, aradaki tutar/fiyat sütunlarıyla
    karışmayı önlüyor. Yeni bir üst bölüme (IV-, V- ...) geçilince satır
    bazında duruyoruz - sayfa genelinde arama yapmak, aynı sayfada bölüm
    geçişinden ÖNCE gelen geçerli satırları da atlamasına yol açıyordu.
    """
    doc = _open(pdf)
    page_no = _find_anchor_page(doc, _HOLDINGS_ANCHOR)
    if page_no is None:
        return pd.DataFrame(columns=["kod", "agirlik_pct"])

    records = []
    weight_x: float | None = None
    section_relative = False
    for pno in range(page_no, len(doc)):
        rows = _page_rows(doc[pno])
        found = _weight_column_x(rows)
        if found is not None:
            weight_x, section_relative = found

        stopped = False
        for row in rows:
            first = row[0].text.strip()
            if pno > page_no and _NEW_SECTION_ROW.match(first):
                stopped = True
                break
            if len(row) < 3 or weight_x is None:
                continue
            if first in _NON_INSTRUMENT_CODES or not re.match(r"^[A-ZÇĞİÖŞÜ0-9]{3,6}$", first):
                continue
            numeric_spans = [(abs(s.x - weight_x), s.text) for s in row if _NUMBER.match(s.text)]
            if not numeric_spans:
                continue
            _, best = min(numeric_spans, key=lambda p: p[0])
            raw = best.replace("%", "").strip()
            raw = raw.replace(".", "").replace(",", ".") if "," in raw else raw
            try:
                pct = float(raw)
            except ValueError:
                continue
            records.append({"kod": first, "agirlik_pct": pct})

        if stopped:
            break

    holdings = pd.DataFrame(records)
    if section_relative and not holdings.empty:
        equity_pct = parse_allocation(pdf).get("Hisse Senedi")
        if equity_pct:
            holdings["agirlik_pct"] = holdings["agirlik_pct"] * equity_pct / 100

    return holdings


_MONTHS = {
    "OCAK": "Ocak", "ŞUBAT": "Şubat", "MART": "Mart", "NİSAN": "Nisan",
    "MAYIS": "Mayıs", "HAZİRAN": "Haziran", "TEMMUZ": "Temmuz", "AĞUSTOS": "Ağustos",
    "EYLÜL": "Eylül", "EKİM": "Ekim", "KASIM": "Kasım", "ARALIK": "Aralık",
}
_MONTHS_FOLDED = {_fold_tr(k): v for k, v in _MONTHS.items()}
_PERIOD = re.compile(
    "(" + "|".join(_MONTHS) + r")" r"[\s\-]*(\d{4})",
    re.IGNORECASE,
)


def parse_period(pdf: PdfSource) -> str | None:
    """PDF'in ait olduğu ay/yılı bulmaya çalışır (örn. 'Haziran-2026')."""
    doc = _open(pdf)
    match = _PERIOD.search(doc[0].get_text())
    if not match:
        return None
    # `.title()` yerelden bağımsızdır ve "HAZİRAN" gibi Türkçe noktalı İ
    # içeren kelimeleri yanlış küçük harfe çevirir (örn. "Hazi̇ran") -
    # bu yüzden sabit bir eşleme kullanıyoruz.
    month = _MONTHS_FOLDED.get(_fold_tr(match.group(1)), match.group(1).title())
    return f"{month}-{match.group(2)}"
