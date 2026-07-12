"""İş Yatırım üzerinden BIST şirketlerinin finansal tablo verisi.

`isyatirimhisse.fetch_financials` çağrısı SYMBOL, FINANCIAL_ITEM_CODE,
FINANCIAL_ITEM_NAME_TR, FINANCIAL_ITEM_NAME_EN ve her çeyrek için bir kolon
("2024/3", "2024/6", ...) içeren geniş (wide) formatta bir DataFrame döndürür.
Kalem isimleri XI_29/UFRS/UFRS_K finansal gruplarına göre değişebildiğinden,
standart kalemler (hasılat, net kar vb.) burada anahtar kelime araması ile
esnek şekilde bulunur.
"""

from __future__ import annotations

import re

import pandas as pd
from isyatirimhisse import fetch_financials as _fetch_financials

# Metrik adı -> FINANCIAL_ITEM_NAME_TR içinde aranacak, öncelik sırasına göre
# anahtar kelimeler. Finansal grup/sektöre göre terminoloji değişebildiği için
# birden fazla aday tutulur; ilk eşleşen kullanılır.
METRIC_KEYWORDS: dict[str, list[str]] = {
    "Hasılat": ["hasılat", "satış gelirleri", "esas faaliyet gelirleri"],
    "Brüt Kar": ["brüt kar"],
    "Esas Faaliyet Karı": ["esas faaliyet karı", "faaliyet karı"],
    "Net Dönem Karı": ["net dönem karı", "dönem net karı", "net dönem kar/zararı"],
    "Toplam Varlıklar": ["toplam varlıklar", "aktif toplamı"],
    "Dönen Varlıklar": ["dönen varlıklar"],
    "Kısa Vadeli Yükümlülükler": ["kısa vadeli yükümlülükler"],
    "Toplam Yükümlülükler": ["toplam yükümlülükler", "pasif toplamı"],
    "Özkaynaklar": ["ana ortaklığa ait özkaynaklar", "özkaynaklar"],
}

QUARTER_COL_RE = re.compile(r"^\d{4}/(3|6|9|12)$")


def get_quarter_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if QUARTER_COL_RE.match(str(c))]
    return sorted(cols, key=lambda c: (int(c.split("/")[0]), int(c.split("/")[1])))


def fetch(
    symbols: list[str] | str,
    start_year: int,
    end_year: int,
    exchange: str = "TRY",
    financial_group: str = "1",
) -> pd.DataFrame:
    return _fetch_financials(
        symbols=symbols,
        start_year=start_year,
        end_year=end_year,
        exchange=exchange,
        financial_group=financial_group,
    )


def find_metric_row(df: pd.DataFrame, symbol: str, metric: str) -> pd.Series | None:
    """Bir sembol için verilen standart metriğe en iyi eşleşen satırı bulur."""
    symbol_df = df[df["SYMBOL"] == symbol]
    if symbol_df.empty:
        return None
    names = symbol_df["FINANCIAL_ITEM_NAME_TR"].astype(str).str.lower()
    for keyword in METRIC_KEYWORDS.get(metric, [metric.lower()]):
        mask = names.str.contains(keyword, na=False)
        if mask.any():
            return symbol_df.loc[mask].iloc[0]
    return None


def metric_series(df: pd.DataFrame, symbol: str, metric: str) -> pd.Series:
    """Bir metriğin tüm çeyreklerdeki değerlerini (çeyrek etiketi -> değer) döndürür."""
    row = find_metric_row(df, symbol, metric)
    if row is None:
        return pd.Series(dtype=float)
    quarters = get_quarter_columns(df)
    values = pd.to_numeric(row[quarters], errors="coerce")
    return values.dropna()


def latest_value(df: pd.DataFrame, symbol: str, metric: str) -> float | None:
    series = metric_series(df, symbol, metric)
    if series.empty:
        return None
    return float(series.iloc[-1])


def qoq_growth(df: pd.DataFrame, symbol: str, metric: str) -> float | None:
    """Metriğin son çeyrekte bir önceki çeyreğe göre yüzde değişimi."""
    series = metric_series(df, symbol, metric)
    if len(series) < 2:
        return None
    prev, last = series.iloc[-2], series.iloc[-1]
    if prev == 0:
        return None
    return float((last / prev - 1) * 100)


def pivot_symbol_table(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Bir sembolün tüm finansal tablo kalemlerini kalem x çeyrek pivot olarak döndürür."""
    symbol_df = df[df["SYMBOL"] == symbol]
    if symbol_df.empty:
        return pd.DataFrame()
    quarters = get_quarter_columns(df)
    pivot = symbol_df.set_index("FINANCIAL_ITEM_NAME_TR")[quarters]
    return pivot.apply(pd.to_numeric, errors="coerce")
