"""İş Yatırım günlük hisse/endeks fiyat verisi ve getiri hesaplamaları."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import pandas as pd
from isyatirimhisse import fetch_stock_data as _fetch_stock_data
from isyatirimhisse import fetch_index_data as _fetch_index_data

CLOSE_COL = "HGDG_KAPANIS"
SYMBOL_COL = "HGDG_HS_KODU"
DATE_COL = "HGDG_TARIH"

MAX_PARALLEL_REQUESTS = 10


def fetch_stock_prices(symbols: list[str], start: date, end: date) -> pd.DataFrame:
    """Birden fazla sembolün fiyatını paralel çeker.

    `isyatirimhisse.fetch_stock_data` sembolleri kendi içinde sırayla
    (tek tek HTTP isteğiyle) çekiyor - çok sayıda sembolde (örn. BIST30)
    bu ciddi yavaşlığa yol açıyordu. Burada her sembolü ayrı bir thread'de
    isteyip sonuçları birleştiriyoruz.
    """
    start_str = start.strftime("%d-%m-%Y")
    end_str = end.strftime("%d-%m-%Y")

    if len(symbols) <= 1:
        frames = [_fetch_stock_data(symbols=symbols, start_date=start_str, end_date=end_str)] if symbols else []
    else:
        frames = []
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_REQUESTS) as pool:
            futures = {
                pool.submit(_fetch_stock_data, symbols=[sym], start_date=start_str, end_date=end_str): sym
                for sym in symbols
            }
            for future in as_completed(futures):
                try:
                    frames.append(future.result())
                except ValueError:
                    continue  # bu sembol için veri yok, atla

    if not frames:
        raise ValueError("No data was fetched for any symbol. Please check the symbols and date ranges.")

    df = pd.concat(frames, ignore_index=True)
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
