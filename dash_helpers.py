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
        st.subheader("Életkor és nem szerinti eloszlás")

        age_gender_pivot = (
            report_df.groupby(["Életkor csoport", "Nem"], observed=True)
            .size()
            .reset_index(name="Count")
            .pivot_table(index="Életkor csoport", columns="Nem", values="Count", observed=True)
            .fillna(0)
        )

        age_gender_pivot = age_gender_pivot.sort_index()
        genders = age_gender_pivot.columns.tolist()
        gender_colors = {"Férfi": "#3498db", "Nő": "#e74c3c"}

        fig = go.Figure()
        for gender in genders:
            fig.add_trace(
                go.Bar(
                    name=gender,
                    x=age_gender_pivot.index.tolist(),
                    y=age_gender_pivot[gender].tolist(),
                    marker={"color": gender_colors.get(gender, "#95a5a6")},
                    text=[int(v) if v > 0 else "" for v in age_gender_pivot[gender].tolist()],
                    textposition="inside",
                    hovertemplate=(
                        f"<b>Életkor:</b> %{{x}} év<br>"
                        f"<b>Nem:</b> {gender}<br>"
                        f"<b>Betegek száma:</b> %{{y}}<br>"
                        f"<extra></extra>"
                    ),
                ),
            )

        fig.update_layout(
            xaxis_title="Életkor (év)",
            yaxis_title="Betegek száma",
            template="plotly_white",
            height=600,
            margin={"l": 50, "r": 20, "t": 20, "b": 50},
            hovermode="x unified",
            barmode="stack",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
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

        st.markdown("---")
        st.subheader("Nem szerinti eloszlás")
        gender_dist = report_df["Nem"].value_counts()
        for gender, count in gender_dist.items():
            st.write(f"**{gender}:** {count} ({count / len(report_df) * 100:.2f}%)")


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


def display_oeno_distribution_chart(report_df: pd.DataFrame, oeno_codes: dict[str, str]) -> None:
    """Display the OENO distribution chart for the dashboard.

    Args:
        report_df: The report DataFrame.
        oeno_codes: Dictionary of OENO codes and names.

    """
    oeno_distribution = get_distribution(report_df, "Beavatkozás OENO kód")
    min_count: int = int(round(sum(oeno_distribution.values()) * 0.01, 0))
    filtered_oeno_distribution: dict[str, int] = {}
    for k, v in oeno_distribution.items():
        if v > min_count:
            try:
                filtered_oeno_distribution[oeno_codes[k]] = v
            except KeyError:
                filtered_oeno_distribution[k] = v

    st.subheader("Beavatkozás OENO kód szerinti eloszlás")
    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=list[str](filtered_oeno_distribution.keys()),
            values=list[int](filtered_oeno_distribution.values()),
            textinfo="label+percent",
        ),
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)


def display_sidebar() -> None:
    """Display the sidebar for the dashboard."""
    st.sidebar.header("📊 Dashboardok")
    st.sidebar.markdown("---")
    st.sidebar.markdown("[Életkor és nem](#eletkor-es-nem-szerinti-eloszlas)")
    st.sidebar.markdown("[Indikáló BNO kód](#indikalo-bno-kod-szerinti-eloszlas)")
    st.sidebar.markdown("[Beavatkozás OENO kód](#beavatkozas-oeno-kod-szerinti-eloszlas)")
