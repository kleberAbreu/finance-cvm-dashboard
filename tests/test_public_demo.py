"""Exercise the public pages, filters, KPIs and administrative boundary."""
from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from src.publication import PUBLIC_PAGES

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def public_mode(monkeypatch):
    monkeypatch.setenv('CVM_DASHBOARD_PUBLIC', '1')
    from src.data.loader import load_and_prepare_base, load_parquet_data
    load_and_prepare_base.clear()
    load_parquet_data.clear()


@pytest.mark.parametrize('path,title,url', PUBLIC_PAGES)
def test_public_pages_render_without_errors(path, title, url):
    app = AppTest.from_file(str(ROOT / path), default_timeout=25).run()
    assert not app.exception, [e.message for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    assert len(app.title) >= 1


def test_overview_metrics_match_independent_sample_calculation():
    raw = pd.read_parquet(ROOT / 'data/sample/base_consolidada.parquet')
    raw = raw[raw['DT_FIM_EXERC'] == raw['DT_FIM_EXERC'].max()]
    app = AppTest.from_file(str(ROOT / PUBLIC_PAGES[0][0]), default_timeout=25).run()
    metric_values = {m.label: m.value for m in app.metric}
    assert metric_values['Empresas'] == str(raw.Ticker.nunique())
    # The whole market is displayed in trillions, rounded to two decimals.
    value = metric_values['Market Cap Total']
    assert value.endswith(' tri')
    displayed = float(value.replace('R$', '').replace('tri', '').replace(',', '.').strip())
    assert abs(displayed * 1e12 - raw.Market_Cap.sum()) <= 0.0051e12
    assert float(metric_values['P/E Mediano'].replace('x', '').replace(',', '.')) == pytest.approx(raw.P_E.median(), abs=0.0051)


def test_ticker_filter_changes_company_population():
    app = AppTest.from_file(str(ROOT / PUBLIC_PAGES[0][0]), default_timeout=25).run()
    app.multiselect(key='ticker_filter').set_value(['PETR4']).run()
    assert not app.exception
    assert not app.error
    metrics = {m.label: m.value for m in app.metric}
    assert metrics['Empresas'] == '1'


def test_pipeline_stops_before_importing_execution_controls():
    app = AppTest.from_file(str(ROOT / 'pages/07_pipeline_execution.py')).run()
    assert not app.exception
    assert not app.button
    assert any('apenas no ambiente local' in i.value for i in app.info)


def test_public_source_ignores_other_valid_parquets(tmp_path):
    from src.data.loader import resolve_data_paths
    p = tmp_path / 'base.parquet'
    pd.DataFrame({'sensitive': ['do-not-load']}).to_parquet(p)
    paths, using_sample, _ = resolve_data_paths(p, p, p)
    assert using_sample
    assert all(path.parent == ROOT / 'data/sample' for path in paths.values())


def test_export_retains_selected_rows_and_demo_provenance():
    from src.components.sidebar import prepare_export_data
    raw = pd.DataFrame({'Ticker': ['PETR4'], 'Market Cap': [500_000_000_000.0]})
    result = prepare_export_data(raw)
    assert result.Ticker.tolist() == ['PETR4']
    assert result['Market Cap'].iloc[0] == 500_000_000_000.0
    assert 'não são cotações atuais' in result.Fonte.iloc[0]
    assert 'reais' in result.Unidade_monetaria.iloc[0]


def test_filters_retain_loss_making_companies_until_explicitly_enabled():
    from src.components.sidebar import apply_filters
    df = pd.DataFrame({'Ticker': ['LOSS3', 'PROFIT3'], 'P/E': [-5.0, 10.0]})
    assert len(apply_filters(df, {'pe': None})) == 2
    assert apply_filters(df, {'pe': (0, 100)}).Ticker.tolist() == ['PROFIT3']


def test_compact_currency_preserves_scale_and_sign():
    from src.utils.formatters import format_currency_compact
    assert format_currency_compact(1_600_000_000_000) == 'R$ 1,60 tri'
    assert format_currency_compact(-500_000_000) == 'R$ -500,00 mi'
    assert format_currency_compact(120_000_000_000) == 'R$ 120,00 bi'
    assert format_currency_compact(None) == 'N/A'


def test_table_currency_keeps_explicit_millions():
    from src.utils.formatters import format_currency
    assert format_currency(500_000_000) == 'R$ 500,0 milhões'


@pytest.mark.parametrize('normalization,expected_unit', [
    ('Nenhuma', '(R$)'), ('Base 100', 'índice base 100'),
    ('% Mudança', 'variação entre períodos, %'),
])
def test_time_series_area_preserves_companies_and_selected_unit(normalization, expected_unit):
    from src.components.charts import create_company_comparison_chart
    df = pd.DataFrame({
        'Ticker': ['AAA3', 'AAA3', 'BBB3', 'BBB3'],
        'Data_Trimestre': pd.to_datetime(['2025-03-31', '2025-06-30'] * 2),
        'Market Cap': [100, 120, 200, 250],
    })
    fig = create_company_comparison_chart(df, 'Market Cap', ['AAA3','BBB3'], 'Área', normalization)
    assert len(fig.data) == 2
    assert list(fig.data[0].y) == [100,120]
    assert list(fig.data[1].y) == [200,250]
    assert all(t.fill == 'tozeroy' for t in fig.data)
    assert expected_unit in fig.layout.yaxis.title.text
    if normalization != 'Nenhuma':
        assert '(R$)' not in fig.layout.yaxis.title.text


def test_public_entrypoint_renders_registered_navigation():
    app = AppTest.from_file(str(ROOT / "public_app.py"), default_timeout=30).run()
    assert not app.exception
    assert not app.error
    assert len(app.get("page_link")) == 7
    assert len(app.metric) == 4
    assert "Visão geral do mercado" in [title.value for title in app.title]
