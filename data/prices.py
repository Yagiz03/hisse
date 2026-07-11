"""İş Yatırım günlük hisse/endeks fiyat verisi ve getiri hesaplamaları."""

from __future__ import annotations

from datetime import date

import pandas as pd
from isyatirimhisse import fetch_stock_data as _fetch_stock_data
from isyatirimhisse import fetch_index_data as _fetch_index_data

CLOSE_COL = "HGDG_KAPANIS"
SYMBOL_COL = "HGDG_HS_KODU"
DATE_COL = "HGDG_TARIH"


def fetch_stock_prices(symbols: list[str], start: date, end: date) -> pd.DataFrame:
    df = _fetch_stock_data(
        symbols=symbols,
        start_date=start.strftime("%d-%m-%Y"),
        end_date=end.strftime("%d-%m-%Y"),
    )
    df[CLOSE_COL] = pd.to_numeric(df[CLOSE_COL], errors="coerce")
    return df


def fetch_index_prices(index: str, start: date, end: date) -> pd.DataFrame:
    df = _fetch_index_data(
        indices=index,
        start_date=start.strftime("%d-%m-%Y"),
        end_date=end.strftime("%d-%m-%Y"),
    )
    df["VALUE"] = pd.to_numeric(df["VALUE"], errors="coerce")
    return df


def period_return(df: pd.DataFrame, symbol: str) -> float | None:
    """Bir sembolün seçilen aralıktaki toplam yüzde getirisi."""
    sub = df[df[SYMBOL_COL] == symbol].sort_values(DATE_COL)
    closes = sub[CLOSE_COL].dropna()
    if len(closes) < 2:
        return None
    return float((closes.iloc[-1] / closes.iloc[0] - 1) * 100)


def daily_returns(df: pd.DataFrame, symbol: str) -> pd.Series:
    """Sembolün tarihe göre indekslenmiş günlük yüzde getiri serisi."""
    sub = df[df[SYMBOL_COL] == symbol].sort_values(DATE_COL).set_index(DATE_COL)
    return sub[CLOSE_COL].pct_change().dropna()
