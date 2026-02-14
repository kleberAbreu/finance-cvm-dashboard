"""
Limpeza, transformações e filtros de dados.
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime


def clean_dataframe(df: pd.DataFrame, remove_inf: bool = True, remove_na: bool = False) -> pd.DataFrame:
    """
    Limpa DataFrame removendo infinitos e opcionalmente NaN.

    Args:
        df: DataFrame original
        remove_inf: Remover valores infinitos
        remove_na: Remover valores NaN

    Returns:
        DataFrame limpo
    """
    df_clean = df.copy()

    if remove_inf:
        # Substituir inf por NaN
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)

    if remove_na:
        # Remover linhas com qualquer NaN
        df_clean = df_clean.dropna()

    return df_clean


def filter_by_date_range(df: pd.DataFrame, start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         date_col: str = 'Data_Trimestre') -> pd.DataFrame:
    """
    Filtra DataFrame por intervalo de datas.

    Args:
        df: DataFrame original
        start_date: Data inicial (inclusive)
        end_date: Data final (inclusive)
        date_col: Nome da coluna de data

    Returns:
        DataFrame filtrado
    """
    df_filtered = df.copy()

    if date_col not in df_filtered.columns:
        return df_filtered

    # Converter datas para pandas Timestamp se necessário
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        df_filtered = df_filtered[df_filtered[date_col] >= start_date]

    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        df_filtered = df_filtered[df_filtered[date_col] <= end_date]

    return df_filtered


def filter_by_tickers(df: pd.DataFrame, tickers: List[str],
                      ticker_col: str = 'Ticker') -> pd.DataFrame:
    """
    Filtra DataFrame por lista de tickers.

    Args:
        df: DataFrame original
        tickers: Lista de tickers
        ticker_col: Nome da coluna de ticker

    Returns:
        DataFrame filtrado
    """
    if not tickers or ticker_col not in df.columns:
        return df

    return df[df[ticker_col].isin(tickers)].copy()


def filter_by_sectors(df: pd.DataFrame, sectors: List[str],
                      sector_col: str = 'Tipo') -> pd.DataFrame:
    """
    Filtra DataFrame por lista de setores.

    Args:
        df: DataFrame original
        sectors: Lista de setores
        sector_col: Nome da coluna de setor

    Returns:
        DataFrame filtrado
    """
    if not sectors or sector_col not in df.columns:
        return df

    return df[df[sector_col].isin(sectors)].copy()


def filter_by_metric_range(df: pd.DataFrame, metric_col: str,
                          min_value: Optional[float] = None,
                          max_value: Optional[float] = None) -> pd.DataFrame:
    """
    Filtra DataFrame por intervalo de valores de uma métrica.

    Args:
        df: DataFrame original
        metric_col: Nome da coluna da métrica
        min_value: Valor mínimo (inclusive)
        max_value: Valor máximo (inclusive)

    Returns:
        DataFrame filtrado
    """
    if metric_col not in df.columns:
        return df

    df_filtered = df.copy()

    if min_value is not None:
        df_filtered = df_filtered[df_filtered[metric_col] >= min_value]

    if max_value is not None:
        df_filtered = df_filtered[df_filtered[metric_col] <= max_value]

    return df_filtered


def get_top_n_by_metric(df: pd.DataFrame, metric_col: str, n: int = 10,
                       ascending: bool = False, group_col: Optional[str] = None) -> pd.DataFrame:
    """
    Retorna top N registros por uma métrica.

    Args:
        df: DataFrame original
        metric_col: Coluna para ranking
        n: Número de registros
        ascending: Ordenar em ordem crescente
        group_col: Coluna para agrupar antes de pegar top N

    Returns:
        DataFrame com top N
    """
    if metric_col not in df.columns:
        return df

    df_clean = df.dropna(subset=[metric_col])

    if group_col is not None and group_col in df.columns:
        # Pegar valor mais recente de cada grupo
        df_clean = df_clean.sort_values('Data_Trimestre').groupby(group_col).tail(1)

    df_sorted = df_clean.sort_values(metric_col, ascending=ascending)

    return df_sorted.head(n)


def get_latest_quarter_data(df: pd.DataFrame, date_col: str = 'Data_Trimestre') -> pd.DataFrame:
    """
    Retorna dados do trimestre mais recente.

    Args:
        df: DataFrame original
        date_col: Nome da coluna de data

    Returns:
        DataFrame com dados mais recentes
    """
    if date_col not in df.columns:
        return df

    latest_date = df[date_col].max()
    return df[df[date_col] == latest_date].copy()


def aggregate_by_sector(df: pd.DataFrame, metrics: List[str],
                       sector_col: str = 'Tipo',
                       agg_methods: dict = None) -> pd.DataFrame:
    """
    Agrega dados por setor.

    Args:
        df: DataFrame original
        metrics: Lista de métricas para agregar
        sector_col: Nome da coluna de setor
        agg_methods: Dicionário {métrica: método} (padrão: mediana)

    Returns:
        DataFrame agregado por setor
    """
    if sector_col not in df.columns:
        return pd.DataFrame()

    # Métodos de agregação padrão
    if agg_methods is None:
        agg_methods = {metric: 'median' for metric in metrics}

    # Adicionar contagem de empresas
    agg_dict = {'Ticker': 'nunique'}
    agg_dict.update(agg_methods)

    df_agg = df.groupby(sector_col).agg(agg_dict).reset_index()
    df_agg = df_agg.rename(columns={'Ticker': 'Qtde_Empresas'})

    return df_agg


def calculate_percentile_column(df: pd.DataFrame, metric_col: str,
                                percentile_col: str = None) -> pd.DataFrame:
    """
    Adiciona coluna com percentil de uma métrica.

    Args:
        df: DataFrame original
        metric_col: Coluna da métrica
        percentile_col: Nome da nova coluna (padrão: {metric_col}_Percentil)

    Returns:
        DataFrame com coluna adicional
    """
    if metric_col not in df.columns:
        return df

    df_result = df.copy()

    if percentile_col is None:
        percentile_col = f'{metric_col}_Percentil'

    # Calcular percentil
    df_result[percentile_col] = df_result[metric_col].rank(pct=True) * 100

    return df_result


def add_quarter_year_columns(df: pd.DataFrame, date_col: str = 'Data_Trimestre') -> pd.DataFrame:
    """
    Adiciona colunas de trimestre e ano separadas.

    Args:
        df: DataFrame original
        date_col: Nome da coluna de data

    Returns:
        DataFrame com colunas adicionais
    """
    if date_col not in df.columns:
        return df

    df_result = df.copy()

    df_result['Ano'] = df_result[date_col].dt.year
    df_result['Quarter'] = df_result[date_col].dt.quarter
    df_result['Trimestre_Label'] = df_result.apply(
        lambda row: f"Q{row['Quarter']} {row['Ano']}" if pd.notna(row[date_col]) else None,
        axis=1
    )

    return df_result


def remove_outliers(df: pd.DataFrame, metric_col: str, method: str = 'iqr',
                   threshold: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers de um DataFrame baseado em uma métrica.

    Args:
        df: DataFrame original
        metric_col: Coluna para detecção de outliers
        method: Método de detecção ('iqr' ou 'zscore')
        threshold: Threshold de detecção

    Returns:
        DataFrame sem outliers
    """
    from src.utils.validators import detect_outliers

    if metric_col not in df.columns:
        return df

    outliers = detect_outliers(df[metric_col], method=method, threshold=threshold)
    return df[~outliers].copy()


def merge_with_sector_benchmarks(df: pd.DataFrame, df_setores: pd.DataFrame,
                                 sector_col: str = 'Tipo') -> pd.DataFrame:
    """
    Faz merge do DataFrame com benchmarks setoriais.

    Args:
        df: DataFrame de empresas
        df_setores: DataFrame de setores
        sector_col: Nome da coluna de setor

    Returns:
        DataFrame merged com sufixo _Setor para métricas setoriais
    """
    if sector_col not in df.columns or sector_col not in df_setores.columns:
        return df

    df_merged = df.merge(
        df_setores,
        on=sector_col,
        how='left',
        suffixes=('', '_Setor')
    )

    return df_merged
