"""Streamlit cache sarmalayıcıları - TEFAS istemcisini her rerun'da yeniden
kurmamak ve aynı gün içinde tekrar tekrar aynı veriyi çekmemek için."""

from datetime import date

import pandas as pd
import streamlit as st

from data import financials as _financials
from data import kap as _kap
from data import kap_fetch as _kap_fetch
from data import prices as _prices

CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 saat
KAP_FETCH_TTL_SECONDS = 24 * 60 * 60  # 24 saat


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_financials(
    symbols: list[str], start_year: int, end_year: int, exchange: str, financial_group: str
) -> pd.DataFrame:
    return _financials.fetch(symbols, start_year, end_year, exchange, financial_group)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_stock_prices(symbols: list[str], start: date, end: date) -> pd.DataFrame:
    return _prices.fetch_stock_prices(symbols, start, end)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_index_prices(index: str, start: date, end: date) -> pd.DataFrame:
    return _prices.fetch_index_prices(index, start, end)


@st.cache_data(show_spinner=False)
def parse_kap_allocation(pdf_bytes: bytes) -> dict[str, float]:
    return _kap.parse_allocation(pdf_bytes)


@st.cache_data(show_spinner=False)
def parse_kap_period(pdf_bytes: bytes) -> str | None:
    return _kap.parse_period(pdf_bytes)


@st.cache_data(ttl=KAP_FETCH_TTL_SECONDS, show_spinner=False)
def fetch_kap_allocation_pdf(fund_code: str) -> bytes:
    return _kap_fetch.KapAutoFetcher().fetch_latest_allocation_pdf(fund_code)
