"""Data ingestion and processing for the dashboard.

This module contains functions for reading data from the CSV and Excel files,
and for processing the data into a format suitable for the dashboard.

"""

import csv
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pandas as pd
import xlrd

EF_COLS_TO_KEEP = [
    "Időszak",
    "Fekvő / Járóbeteg",
    "Térítési kategória",
    "Születési dátum",
    "Nem",
    "Állampolgárság",
    "Törzsszám / Naplószám",
    "Ellátó szervezeti egység",
    "Műtéti napló száma",
    "Beutaló szervezeti egység",
    "Beutaló orvos pecsétszáma",
    "Beutalást megalapozó adat",
    "Beavatkozás dátuma",
    "Eszköz / Eljárás kódja",
    "Csoport",
    "Pótkód",
    "Kiegészítő kód",
    "Beavatkozás OENO kód",
    "Indikáló BNO kód",
    "Jelentett mennyiség",
    "Jelentett érték",
    "Számlát kiállító cég",
    "Számla száma",
    "Számla dátuma",
    "Elszámolt mennyiség",
    "Elszámolt érték",
    "Fin. státusz",
    "Hibaüzenetek",
    "Jogviszony ellenőrzés visszavonása",
    "Jogviszony ellenőrzési díj",
    "Kassza azonosító",
]


def read_bno_codes(
    csv_path: Path = Path("data/BNO.csv"),
    code_column_name: str = "KOD10,C,5",
    name_column_name: str = "NEV,C,150",
) -> dict[str, str]:
    """Read BNO codes from the given CSV file.

    Args:
        csv_path: The path to the CSV file containing the BNO codes.
        code_column_name: The name of the column containing the BNO codes.
        name_column_name: The name of the column containing the BNO names.

    Returns:
        A dictionary containing the BNO codes.

    """
    with csv_path.open("r") as file:
        reader: csv.DictReader = csv.DictReader(file)
        return {row[code_column_name].strip(): row[name_column_name].strip().replace("ï", "ő") for row in reader}


def read_ef_data(data_folder: Path = Path("data/ef"), *, drop_cols: bool = True) -> pd.DataFrame:
    """Read EF data (.xls files) from the given data folder.

    Args:
        data_folder: The folder containing the EF data (.xls files).
        drop_cols: Whether to drop the columns that are not needed.

    Returns:
        A pandas DataFrame containing the EF data.

    """
    ef_df: pd.DataFrame = pd.concat(
        [
            pd.read_excel(xlrd.open_workbook(file, ignore_workbook_corruption=True))
            for file in data_folder.glob("*.xls")
        ],
    )
    if drop_cols:
        ef_df = ef_df[EF_COLS_TO_KEEP]
    return ef_df


def add_age_column(
    ef_df: pd.DataFrame,
    dob_column_name: str = "Születési dátum",
    age_column_name: str = "Életkor",
) -> pd.DataFrame:
    """Convert date of birth to datetime and calculate age.

    Args:
        ef_df: Pandas DataFrame containing the data.
        dob_column_name: The name of the column containing the date of birth.
        age_column_name: The name of the column for storing the age.

    Returns:
        The pandas DataFrame with the age column.

    """
    ef_df[dob_column_name] = pd.to_datetime(ef_df[dob_column_name])
    ef_df[age_column_name] = ((datetime.now() - ef_df[dob_column_name]).dt.days / 365.25).astype(int)
    return ef_df


def add_age_bins(
    ef_df: pd.DataFrame,
    age_column_name: str = "Életkor",
    age_bin_column_name: str = "Életkor csoport",
    bin_size: int = 5,
) -> pd.DataFrame:
    """Add age bins to the given pandas DataFrame.

    Args:
        ef_df: Pandas DataFrame containing the data.
        age_column_name: The name of the column containing the age.
        age_bin_column_name: The name of the column for storing the age bins.
        bin_size: The size of the age bins.

    Returns:
        The pandas DataFrame with the age bins column.

    """
    age_distribution: pd.Series = ef_df[age_column_name].value_counts().sort_index()
    start_bin: int = (age_distribution.index.min() // bin_size) * bin_size
    end_bin: int = ((age_distribution.index.max() // bin_size) + 1) * bin_size
    bins: list[int] = list[int](range(start_bin, end_bin + 1, bin_size))

    ef_df[age_bin_column_name] = pd.cut(
        ef_df[age_column_name],
        bins=bins,
        labels=[f"{b}-{b + bin_size - 1}" for b in bins[:-1]],
        right=True,
        include_lowest=True,
        ordered=True,
    )
    return ef_df


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
    errors: pd.DataFrame = ef_df[(ef_df[error_column_name] == 0) & (ef_df["Jelentett érték"] != 0)]
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


def get_report() -> pd.DataFrame:
    """Get the report data.

    Returns:
        The pandas DataFrame with the report data.

    """
    ef_df: pd.DataFrame = read_ef_data()
    ef_df = add_age_column(ef_df)
    ef_df = add_age_bins(ef_df)
    return deepcopy(ef_df)
