"""Main dashboard application."""

import locale

import streamlit as st

from dash_helpers import (
    display_age_distribution_chart,
    display_bno_distribution_chart,
    display_metrics,
    display_oeno_distribution_chart,
    display_sidebar,
)
from report import get_error_df, get_report, read_bno_codes, read_oeno_codes

try:
    locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, "hu_HU")
    except locale.Error:
        locale.setlocale(locale.LC_ALL, "")

REPORT = get_report()
ERROR_DF = get_error_df(REPORT)
BNO_CODES = read_bno_codes()
OENO_CODES = read_oeno_codes()
PAGE_TITLE = "Dashboard Program"
PAGE_ICON = "🏥"


st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
display_sidebar()
st.title(f"{PAGE_ICON} {PAGE_TITLE}")
st.markdown("---")
display_metrics(REPORT, ERROR_DF)
st.markdown("---")
display_age_distribution_chart(REPORT)
st.markdown("---")
display_bno_distribution_chart(REPORT, BNO_CODES)
st.markdown("---")
display_oeno_distribution_chart(REPORT, OENO_CODES)
st.markdown("---")
st.header("Hibás rekordok")
st.dataframe(ERROR_DF, use_container_width=True, hide_index=True)
