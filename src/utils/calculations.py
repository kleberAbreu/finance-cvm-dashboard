"""
Cálculos financeiros e estatísticos.
"""
import pandas as pd
import numpy as np
from typing import Union, List


def calculate_ttm(df: pd.DataFrame, metric_col: str, date_col: str = 'Data_Trimestre',
                  group_col: str = 'Ticker') -> pd.Series:
    """
    Calcula Trailing Twelve Months (TTM) para uma métrica.

    Args:
        df: DataFrame com dados trimestrais
        metric_col: Nome da coluna com a métrica
        date_col: Nome da coluna de data
        group_col: Coluna de agrupamento (empresa)

    Returns:
        Série com valores TTM
    """
    df = df.sort_values([group_col, date_col])

    ttm = df.groupby(group_col)[metric_col].rolling(
        window=4,
        min_periods=4
    ).sum().reset_index(level=0, drop=True)

    return ttm


def calculate_cagr(start_value: float, end_value: float, periods: int) -> float:
    """
    Calcula Compound Annual Growth Rate (CAGR).

    Args:
        start_value: Valor inicial
        end_value: Valor final
        periods: Número de períodos (anos)

    Returns:
        CAGR como decimal (0.10 = 10%)
    """
    if start_value <= 0 or end_value <= 0 or periods <= 0:
        return np.nan

    cagr = (end_value / start_value) ** (1 / periods) - 1
    return cagr


def calculate_yoy_growth(df: pd.DataFrame, metric_col: str, date_col: str = 'Data_Trimestre',
                        group_col: str = 'Ticker') -> pd.Series:
    """
    Calcula crescimento Year-over-Year.

    Args:
        df: DataFrame com dados trimestrais
        metric_col: Nome da coluna com a métrica
        date_col: Nome da coluna de data
        group_col: Coluna de agrupamento

    Returns:
        Série com crescimento YoY (decimal)
    """
    df = df.sort_values([group_col, date_col])

    yoy = df.groupby(group_col)[metric_col].pct_change(periods=4)

    return yoy


def calculate_percentile_rank(series: pd.Series, value: float) -> float:
    """
    Calcula o percentil de um valor dentro de uma série.

    Args:
        series: Série de valores
        value: Valor para calcular percentil

    Returns:
        Percentil (0-100)
    """
    clean_series = series.dropna()
    if len(clean_series) == 0:
        return np.nan

    percentile = (clean_series < value).sum() / len(clean_series) * 100
    return percentile


def calculate_volatility(series: pd.Series) -> float:
    """
    Calcula volatilidade (desvio padrão) de uma série temporal.

    Args:
        series: Série de valores

    Returns:
        Desvio padrão
    """
    return series.std()


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calcula Sharpe Ratio.

    Args:
        returns: Série de retornos
        risk_free_rate: Taxa livre de risco

    Returns:
        Sharpe ratio
    """
    excess_returns = returns - risk_free_rate
    if excess_returns.std() == 0:
        return np.nan

    sharpe = excess_returns.mean() / excess_returns.std()
    return sharpe


def weighted_average(values: pd.Series, weights: pd.Series) -> float:
    """
    Calcula média ponderada.

    Args:
        values: Série de valores
        weights: Série de pesos

    Returns:
        Média ponderada
    """
    # Remover NaN e infinitos
    mask = ~(values.isna() | weights.isna() |
             values.isin([float('inf'), float('-inf')]) |
             weights.isin([float('inf'), float('-inf')]))

    clean_values = values[mask]
    clean_weights = weights[mask]

    if len(clean_values) == 0 or clean_weights.sum() == 0:
        return np.nan

    return (clean_values * clean_weights).sum() / clean_weights.sum()


def normalize_series(series: pd.Series, method: str = 'base100') -> pd.Series:
    """
    Normaliza série temporal.

    Args:
        series: Série de valores
        method: Método ('base100', 'pct_change', 'zscore')

    Returns:
        Série normalizada
    """
    if method == 'base100':
        first_valid = series.dropna().iloc[0] if len(series.dropna()) > 0 else 1
        return (series / first_valid) * 100

    elif method == 'pct_change':
        return series.pct_change() * 100

    elif method == 'zscore':
        mean = series.mean()
        std = series.std()
        if std == 0:
            return pd.Series([0] * len(series), index=series.index)
        return (series - mean) / std

    else:
        raise ValueError(f"Método desconhecido: {method}")


def calculate_correlation_matrix(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Calcula matriz de correlação para colunas especificadas.

    Args:
        df: DataFrame
        columns: Lista de colunas numéricas

    Returns:
        DataFrame com matriz de correlação
    """
    # Selecionar apenas colunas especificadas e remover infinitos
    df_clean = df[columns].copy()
    df_clean = df_clean.replace([np.inf, -np.inf], np.nan)

    corr_matrix = df_clean.corr(method='pearson')

    return corr_matrix


def calculate_regression_stats(x: pd.Series, y: pd.Series) -> dict:
    """
    Calcula estatísticas de regressão linear simples.

    Args:
        x: Série independente
        y: Série dependente

    Returns:
        Dicionário com slope, intercept, r_value, p_value, std_err
    """
    from scipy import stats

    # Remover NaN e infinitos
    mask = ~(x.isna() | y.isna() |
             x.isin([float('inf'), float('-inf')]) |
             y.isin([float('inf'), float('-inf')]))

    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 2:
        return {
            'slope': np.nan,
            'intercept': np.nan,
            'r_value': np.nan,
            'r_squared': np.nan,
            'p_value': np.nan,
            'std_err': np.nan
        }

    slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)

    return {
        'slope': slope,
        'intercept': intercept,
        'r_value': r_value,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'std_err': std_err
    }
