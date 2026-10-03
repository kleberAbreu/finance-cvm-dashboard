from pathlib import Path

from src.data.loader import (
    get_sample_data_paths,
    load_and_prepare_base,
    load_parquet_data,
    resolve_data_paths,
)
from src.utils.validators import validate_parquet_structure


def test_sample_parquets_have_valid_schema():
    is_valid, errors = validate_parquet_structure(get_sample_data_paths())

    assert is_valid, errors


def test_missing_pipeline_data_falls_back_to_sample(tmp_path):
    missing_base = tmp_path / "missing_base.parquet"
    missing_setores = tmp_path / "missing_setores.parquet"
    missing_mercado = tmp_path / "missing_mercado.parquet"

    paths, using_sample, errors = resolve_data_paths(
        missing_base,
        missing_setores,
        missing_mercado,
    )

    assert using_sample is True
    assert errors
    assert paths["base"].name == "base_consolidada.parquet"
    assert paths["base"].parent == Path("data/sample").resolve()


def test_load_and_prepare_base_uses_sample_when_pipeline_data_is_absent(tmp_path):
    df = load_and_prepare_base(tmp_path / "missing_base.parquet")

    assert not df.empty
    assert {"Ticker", "Empresa", "Data_Trimestre", "Market Cap", "P/E"}.issubset(df.columns)
    assert df["Ticker"].nunique() >= 5


def test_explicit_sample_base_path_loads_companion_sample_files():
    sample_paths = get_sample_data_paths()

    df_base, df_setores, df_mercado = load_parquet_data(base_file=sample_paths["base"])

    assert not df_base.empty
    assert not df_setores.empty
    assert not df_mercado.empty
