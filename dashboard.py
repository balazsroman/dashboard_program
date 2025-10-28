import locale
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from report import get_report

locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
REPORT: pd.DataFrame = get_report()

PAGE_TITLE = "Dashboard Program"
PAGE_ICON = "🏥"


def get_error_df(
    ef_df: pd.DataFrame,
    error_column_name: str = "Elszámolt érték",
    error_message_column_name: str = "Hibaüzenetek",
) -> pd.DataFrame:
    """Get the error DataFrame.

    Args:
        ef_df: Pandas DataFrame containing the data.
        error_column_name: The name of the column containing the error.
        error_message_column_name: The name of the column containing the error message.

    Returns:
        The pandas DataFrame with the error data.

    """
    errors: pd.DataFrame = ef_df[ef_df[error_column_name] == 0]
    return errors.sort_values(by=error_message_column_name)


def get_distribution(
    ef_df: pd.DataFrame,
    column_name: str,
) -> dict[str, int]:
    """Get the distribution of the given column.

    Args:
        ef_df: Pandas DataFrame containing the data.
        column_name: The name of the column to get the distribution of.

    Returns:
        A dictionary containing the distribution of the given column.

    """
    return ef_df[column_name].value_counts().sort_index().to_dict()


TOTAL_FINANCED_AMOUNT = float(REPORT["Elszámolt érték"].sum())
TOTAL_REPORTED_AMOUNT = float(REPORT["Jelentett érték"].sum())
# GENDER_DISTRIBUTION = get_distribution(REPORT, "Nem")
# AGE_DISTRIBUTION = get_distribution(REPORT, "Életkor")
AGE_GROUP_DISTRIBUTION = get_distribution(REPORT, "Életkor csoport")
# OENO_DISTRIBUTION = get_distribution(REPORT, "Beavatkozás OENO kód")
# BNO_DISTRIBUTION = get_distribution(REPORT, "Indikáló BNO kód")

ERROR_DF = get_error_df(REPORT)


st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

st.title(f"{PAGE_ICON} {PAGE_TITLE}")
st.markdown("---")


st.sidebar.header("📊 Dashboardok")
st.sidebar.info("Életkor szerinti eloszlás")


col1, col2 = st.columns(2)
with col1:
    period_start = REPORT["Időszak"].min()
    period_end = REPORT["Időszak"].max()
    formatted_start = datetime.strptime(str(period_start), "%Y%m").strftime("%Y. %B")
    formatted_end = datetime.strptime(str(period_end), "%Y%m").strftime("%Y. %B")
    st.metric("Időszak", f"{formatted_start} - {formatted_end}")
with col2:
    st.metric("Betegek száma", len(REPORT))

col1, col2 = st.columns(2)
with col1:
    st.metric("Finanszírozás összege", locale.currency(TOTAL_FINANCED_AMOUNT, grouping=True))
with col2:
    st.metric("Jelentett érték", locale.currency(TOTAL_REPORTED_AMOUNT, grouping=True))


col1, col2 = st.columns(2)
with col1:
    st.metric(
        "Eltérés",
        f"{locale.currency(TOTAL_FINANCED_AMOUNT - TOTAL_REPORTED_AMOUNT, grouping=True)} ({((TOTAL_FINANCED_AMOUNT - TOTAL_REPORTED_AMOUNT) / TOTAL_REPORTED_AMOUNT * 100):.2f}%)",
    )
with col2:
    st.metric("Hibás rekordok száma", len(ERROR_DF))

st.markdown("---")

col_chart, col_stats = st.columns([3, 1])

with col_chart:
    st.subheader("Életkor szerinti eloszlás")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list[str](AGE_GROUP_DISTRIBUTION.keys()),
            y=list[int](AGE_GROUP_DISTRIBUTION.values()),
            marker={
                "color": list[int](AGE_GROUP_DISTRIBUTION.values()),
                "colorscale": "YlOrRd",
                "showscale": True,
                "colorbar": {"title": "Betegek száma"},
            },
            text=list[int](AGE_GROUP_DISTRIBUTION.values()),
            textposition="outside",
            hovertemplate="<b>Életkor:</b> %{x} év<br>" + "<b>Betegek száma:</b> %{y}<br>" + "<extra></extra>",
        ),
    )

    fig.update_layout(
        xaxis_title="Életkor (év)",
        yaxis_title="Betegek száma",
        template="plotly_white",
        height=500,
        margin={"l": 50, "r": 20, "t": 20, "b": 50},
        hovermode="x unified",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    min_age = REPORT["Életkor"].min()
    max_age = REPORT["Életkor"].max()
    median_age = REPORT["Életkor"].median().astype(int)
    mean_age = REPORT["Életkor"].mean().astype(int)

    st.subheader("Összegzés")
    st.write(f"**Életkor tartomány:** {min_age} - {max_age}")
    st.write(f"**Átlag életkor:** {mean_age}")
    st.write(f"**Medián életkor:** {median_age}")

    st.markdown("---")

    top_ages = sorted(AGE_GROUP_DISTRIBUTION.items(), key=lambda x: x[1], reverse=True)[:3]
    st.subheader("3 leggyakoribb korcsoport")
    for age_group, count in top_ages:
        st.write(f"**{age_group}** év: {count} beteg ({count / len(REPORT) * 100:.2f}%)")
