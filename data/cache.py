"""Streamlit cache sarmalayıcıları - TEFAS istemcisini her rerun'da yeniden
kurmamak ve aynı gün içinde tekrar tekrar aynı veriyi çekmemek için."""

from datetime import date

import pandas as pd
import streamlit as st

from data.tefas import TefasClient
from data import financials as _financials

CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 saat


@st.cache_resource
def get_client() -> TefasClient:
    return TefasClient()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_allocation(fund_code: str, start_date: date, end_date: date) -> pd.DataFrame:
    return get_client().get_fund_allocation(fund_code, start_date, end_date)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_info(fund_code: str, start_date: date, end_date: date) -> pd.DataFrame:
    return get_client().get_fund_info(fund_code, start_date, end_date)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_financials(
    symbols: list[str], start_year: int, end_year: int, exchange: str, financial_group: str
) -> pd.DataFrame:
    return _financials.fetch(symbols, start_year, end_year, exchange, financial_group)
