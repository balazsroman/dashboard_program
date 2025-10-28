"""Helper functions for the dashboard."""

import locale
from datetime import datetime

import pandas as pd  # noqa: TC002
import plotly.graph_objects as go
import streamlit as st

from report import get_distribution


def display_metrics(report_df: pd.DataFrame, error_df: pd.DataFrame) -> None:
    """Display the metrics for the dashboard.

    Args:
        report_df: The report DataFrame.
        error_df: The error DataFrame.

    Returns:
        None.

    """
    total_financed_amount = float(report_df["Elszámolt érték"].sum())
    total_reported_amount = float(report_df["Jelentett érték"].sum())
    col1, col2 = st.columns(2)
    with col1:
        period_start = report_df["Időszak"].min()
        period_end = report_df["Időszak"].max()
        formatted_start = datetime.strptime(str(period_start), "%Y%m").strftime("%Y. %B")
        formatted_end = datetime.strptime(str(period_end), "%Y%m").strftime("%Y. %B")
        st.metric("Időszak", f"{formatted_start} - {formatted_end}")
    with col2:
        st.metric("Betegek száma", f"{len(report_df)} fő")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Finanszírozás összege", locale.currency(total_financed_amount, grouping=True))
    with col2:
        st.metric("Jelentett érték", locale.currency(total_reported_amount, grouping=True))

    col1, col2 = st.columns(2)
    with col1:
        difference = total_financed_amount - total_reported_amount
        st.metric(
            "Eltérés",
            f"{locale.currency(difference, grouping=True)}",
            delta=f"{(difference / total_reported_amount) * 100:.2f}%",
        )
    with col2:
        st.metric(
            "Hibás rekordok száma",
            f"{len(error_df)} db",
            delta=f"{(len(error_df) / len(report_df)) * 100:.2f}%",
            delta_color="inverse",
        )


def display_age_distribution_chart(report_df: pd.DataFrame) -> None:
    """Display the age distribution chart for the dashboard.

    Args:
        report_df: The report DataFrame.

    Returns:
        None.

    """
    age_group_distribution = get_distribution(report_df, "Életkor csoport")
    col_chart, col_stats = st.columns([3, 1])

    with col_chart:
        st.subheader("Életkor szerinti eloszlás")

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=list[str](age_group_distribution.keys()),
                y=list[int](age_group_distribution.values()),
                marker={
                    "color": list[int](age_group_distribution.values()),
                    "colorscale": "YlOrRd",
                    "showscale": True,
                    "colorbar": {"title": "Betegek száma"},
                },
                text=list[int](age_group_distribution.values()),
                textposition="outside",
                hovertemplate="<b>Életkor:</b> %{x} év<br><b>Betegek száma:</b> %{y}<br><extra></extra>",
            ),
        )

        fig.update_layout(
            xaxis_title="Életkor (év)",
            yaxis_title="Betegek száma",
            template="plotly_white",
            height=400,
            margin={"l": 50, "r": 20, "t": 20, "b": 50},
            hovermode="x unified",
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_stats:
        min_age = report_df["Életkor"].min()
        max_age = report_df["Életkor"].max()
        median_age = report_df["Életkor"].median().astype(int)
        mean_age = report_df["Életkor"].mean().astype(int)

        st.subheader("Összegzés")
        st.write(f"**Életkor tartomány:** {min_age} - {max_age}")
        st.write(f"**Átlag életkor:** {mean_age}")
        st.write(f"**Medián életkor:** {median_age}")

        st.markdown("---")

        top_ages = sorted(age_group_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        st.subheader("3 leggyakoribb korcsoport")
        for age_group, count in top_ages:
            st.write(f"**{age_group}** év: {count} beteg ({count / len(report_df) * 100:.2f}%)")


def display_bno_distribution_chart(report_df: pd.DataFrame, bno_codes: dict[str, str]) -> None:
    """Display the BNO distribution chart for the dashboard.

    Args:
        report_df: The report DataFrame.
        bno_codes: Dictionary of BNO codes and names.

    """
    bno_distribution = get_distribution(report_df, "Indikáló BNO kód")
    min_count: int = int(round(sum(bno_distribution.values()) * 0.01, 0))
    filtered_bno_distribution: dict[str, int] = {bno_codes[k]: v for k, v in bno_distribution.items() if v > min_count}

    st.subheader("Indikáló BNO kód szerinti eloszlás")
    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=list[str](filtered_bno_distribution.keys()),
            values=list[int](filtered_bno_distribution.values()),
            textinfo="label+percent",
        ),
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)


def display_sidebar() -> None:
    """Display the sidebar for the dashboard."""
    st.sidebar.header("📊 Dashboardok")
    st.sidebar.markdown("---")
    st.sidebar.markdown("[Életkor](#eletkor-szerinti-eloszlas)")
    st.sidebar.markdown("[Indikáló BNO kód](#indikalo-bno-kod-szerinti-eloszlas)")
