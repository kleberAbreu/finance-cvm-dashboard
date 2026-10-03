"""Policy shared by the isolated public demo and its pages."""
import os


def is_public_demo() -> bool:
    return os.getenv('CVM_DASHBOARD_PUBLIC', '').lower() in {'1', 'true', 'yes', 'on'}


PUBLIC_PAGES = (
    ('pages/01_overview.py', 'Visão geral', 'overview'),
    ('pages/02_company_analysis.py', 'Empresas', 'company_analysis'),
    ('pages/03_sector_comparison.py', 'Setores', 'sector_comparison'),
    ('pages/04_screener.py', 'Screener', 'screener'),
    ('pages/05_time_series.py', 'Séries temporais', 'time_series'),
    ('pages/06_correlations.py', 'Correlações', 'correlations'),
    ('pages/08_pl.py', 'Demonstrações financeiras', 'pl'),
)
