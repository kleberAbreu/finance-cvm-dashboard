import pandas as pd

from src.data.incremental_pipeline import merge_incremental_data
from src.data.loader import load_and_prepare_base
from src.data.preprocessor import (
    filter_by_metric_range,
    filter_by_tickers,
    get_latest_quarter_data,
)
from src.utils.calculations import calculate_regression_stats


def test_core_filters_keep_expected_rows():
    df = load_and_prepare_base()
    ticker = str(df["Ticker"].dropna().astype(str).iloc[0])

    by_ticker = filter_by_tickers(df, [ticker])
    latest = get_latest_quarter_data(by_ticker)
    screened = filter_by_metric_range(latest, "Market Cap", min_value=1)

    assert not by_ticker.empty
    assert by_ticker["Ticker"].astype(str).eq(ticker).all()
    assert latest["Data_Trimestre"].nunique() == 1
    assert len(screened) <= len(latest)


def test_regression_stats_handles_clean_numeric_data():
    stats = calculate_regression_stats(
        pd.Series([1.0, 2.0, 3.0, 4.0]),
        pd.Series([2.0, 4.0, 6.0, 8.0]),
    )

    assert stats["r_squared"] == 1.0
    assert stats["slope"] == 2.0


def test_incremental_merge_replaces_duplicate_quarters(tmp_path):
    existing = pd.DataFrame(
        {
            "CNPJ_CIA": ["1", "1"],
            "DT_FIM_EXERC": pd.to_datetime(["2025-03-31", "2025-06-30"]),
            "Ticker": ["AAA3", "AAA3"],
            "Market_Cap": [100.0, 110.0],
        }
    )
    new = pd.DataFrame(
        {
            "CNPJ_CIA": ["1", "2"],
            "DT_FIM_EXERC": pd.to_datetime(["2025-06-30", "2025-06-30"]),
            "Ticker": ["AAA3", "BBB3"],
            "Market_Cap": [120.0, 210.0],
        }
    )

    parquet_path = tmp_path / "existing.parquet"
    existing.to_parquet(parquet_path, index=False)

    merged = merge_incremental_data(parquet_path, new)

    assert len(merged) == 3
    assert merged.loc[
        (merged["CNPJ_CIA"] == "1") & (merged["DT_FIM_EXERC"] == pd.Timestamp("2025-06-30")),
        "Market_Cap",
    ].iloc[0] == 120.0
