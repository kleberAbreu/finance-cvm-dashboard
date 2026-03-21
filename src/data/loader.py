"""
Carregamento de dados do Excel com cache.
"""
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Tuple, Dict
from config.settings import (
    PARQUET_BASE_FILE, PARQUET_SETORES_FILE, PARQUET_MERCADO_FILE,
    CACHE_TTL
)
from src.utils.validators import validate_parquet_structure, check_data_quality


@st.cache_data(ttl=CACHE_TTL, show_spinner="Carregando dados...")
def load_parquet_data(
    base_file: Path = PARQUET_BASE_FILE,
    setores_file: Path = PARQUET_SETORES_FILE,
    mercado_file: Path = PARQUET_MERCADO_FILE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carrega as três bases de dados de arquivos Parquet com cache.

    Returns:
        Tuple (df_base, df_setores, df_mercado)
    """
    from config.settings import COLUMN_MAPPING_SETORES

    file_paths = {
        'base': base_file,
        'setores': setores_file,
        'mercado': mercado_file
    }

    # Validar estrutura
    is_valid, errors = validate_parquet_structure(file_paths)
    if not is_valid:
        raise ValueError(f"Erro na estrutura do banco de dados (Parquet): {'; '.join(errors)}")

    # Carregar planilhas do Parquet
    df_base = pd.read_parquet(file_paths['base'])
    df_setores = pd.read_parquet(file_paths['setores'])
    df_mercado = pd.read_parquet(file_paths['mercado'])

    # Renomear colunas do resumo setorial
    if not df_setores.empty:
        df_setores = df_setores.rename(columns=COLUMN_MAPPING_SETORES)

    return df_base, df_setores, df_mercado


@st.cache_data(ttl=CACHE_TTL)
def load_and_prepare_base(base_file: Path = PARQUET_BASE_FILE) -> pd.DataFrame:
    """
    Carrega e prepara dados da Base Consolidada.
    Nenhum parsing numérico ou data é necessário, pois o Parquet já preserva os tipos nativos.

    Args:
        base_file: Caminho do arquivo Parquet da Base Consolidada

    Returns:
        DataFrame preparado
    """
    from config.settings import COLUMN_MAPPING

    df_base, _, _ = load_parquet_data(base_file=base_file)

    # Renomear colunas para padronizar
    df_base = df_base.rename(columns=COLUMN_MAPPING)

    # Converter coluna de data
    if 'Data_Trimestre' in df_base.columns:
        df_base['Data_Trimestre'] = pd.to_datetime(df_base['Data_Trimestre'], errors='coerce')

    # Criar coluna Trimestre se não existir
    if 'Trimestre' not in df_base.columns and 'Data_Trimestre' in df_base.columns:
        df_base['Trimestre'] = df_base['Data_Trimestre'].dt.year.astype(str) + 'Q' + df_base['Data_Trimestre'].dt.quarter.astype(str)

    # Converter colunas numéricas
    numeric_cols = [
        'Ativo Total', 'Caixa', 'Dívida Bruta', 'Dívida Líquida',
        'Patrimônio Líquido', 'Receita Líquida', 'CPV', 'Lucro Bruto',
        'Despesas Operacionais', 'EBIT', 'Lucro Líquido', 'Resultado Financeiro',
        'IR', 'D&A', 'EBITDA', 'Preço de Fechamento', 'Qtde Ações',
        'Market Cap', 'Enterprise Value', 'P/E', 'EV/EBITDA', 'P/B', 'DL/EV'
    ]

    for col in numeric_cols:
        if col in df_base.columns:
            df_base[col] = pd.to_numeric(df_base[col], errors='coerce')

    # Converter Qtde Ações de milhões para unidades (se necessário para cálculos)
    # Nota: A coluna já vem em milhões do Excel, mantemos assim
    # Converter qtde ações
    if 'Qtde Ações' in df_base.columns:
        df_base['Qtde Ações'] = df_base['Qtde Ações'] * 1_000_000

    # Otimizar tipos de dados se não for Parquet categórico
    if 'Ticker' in df_base.columns and df_base['Ticker'].dtype != 'category':
        df_base['Ticker'] = df_base['Ticker'].astype('category')
    if 'Empresa' in df_base.columns and df_base['Empresa'].dtype != 'category':
        df_base['Empresa'] = df_base['Empresa'].astype('category')
    if 'Tipo' in df_base.columns and df_base['Tipo'].dtype != 'category':
        df_base['Tipo'] = df_base['Tipo'].astype('category')
    if 'Trimestre' in df_base.columns and df_base['Trimestre'].dtype != 'category':
        df_base['Trimestre'] = df_base['Trimestre'].astype('category')

    # Ordenar por data
    df_base = df_base.sort_values(['Ticker', 'Data_Trimestre'], ignore_index=True)

    return df_base


@st.cache_data(ttl=CACHE_TTL)
def get_data_summary(base_file: Path = PARQUET_BASE_FILE) -> Dict[str, any]:
    """
    Retorna resumo estatístico dos dados.

    Args:
        base_file: Caminho do arquivo Parquet

    Returns:
        Dicionário com estatísticas
    """
    df_base = load_and_prepare_base(base_file)

    summary = {
        'total_records': len(df_base),
        'total_companies': df_base['Ticker'].nunique() if 'Ticker' in df_base.columns else 0,
        'total_sectors': df_base['Tipo'].nunique() if 'Tipo' in df_base.columns else 0,
        'date_range': {
            'min': df_base['Data_Trimestre'].min() if 'Data_Trimestre' in df_base.columns else None,
            'max': df_base['Data_Trimestre'].max() if 'Data_Trimestre' in df_base.columns else None
        },
        'quality': check_data_quality(df_base)
    }

    return summary


@st.cache_data(ttl=CACHE_TTL)
def get_available_tickers(base_file: Path = PARQUET_BASE_FILE) -> list:
    """
    Retorna lista de tickers disponíveis ordenada.

    Args:
        base_file: Caminho do Parquet Mestre

    Returns:
        Lista de tickers
    """
    df_base = load_and_prepare_base(base_file)

    if 'Ticker' not in df_base.columns:
        return []

    # Remover valores nulos e converter para string
    tickers = df_base['Ticker'].dropna().astype(str).unique().tolist()
    tickers = [t for t in tickers if t and t != 'nan']  # Filtrar vazios
    tickers = sorted(tickers)
    return tickers


@st.cache_data(ttl=CACHE_TTL)
def get_available_sectors(base_file: Path = PARQUET_BASE_FILE) -> list:
    """
    Retorna lista de setores disponíveis ordenada.

    Args:
        base_file: Caminho do Parquet Base

    Returns:
        Lista de setores
    """
    df_base = load_and_prepare_base(base_file)

    if 'Tipo' not in df_base.columns:
        return []

    # Remover valores nulos e converter para string
    sectors = df_base['Tipo'].dropna().astype(str).unique().tolist()
    sectors = [s for s in sectors if s and s != 'nan']  # Filtrar vazios
    sectors = sorted(sectors)
    return sectors


@st.cache_data(ttl=CACHE_TTL)
def get_ticker_info(ticker: str, base_file: Path = PARQUET_BASE_FILE) -> Dict[str, any]:
    """
    Retorna informações sobre um ticker específico.

    Args:
        ticker: Código do ticker
        base_file: Caminho do Parquet Base

    Returns:
        Dicionário com informações
    """
    df_base = load_and_prepare_base(base_file)

    ticker_data = df_base[df_base['Ticker'] == ticker]

    if len(ticker_data) == 0:
        return {}

    # Pegar dados mais recentes
    latest = ticker_data.sort_values('Data_Trimestre').iloc[-1]

    info = {
        'ticker': ticker,
        'empresa': latest.get('Empresa', 'N/A'),
        'setor': latest.get('Tipo', 'N/A'),
        'data_mais_recente': latest.get('Data_Trimestre'),
        'market_cap': latest.get('Market Cap'),
        'pe': latest.get('P/E'),
        'ev_ebitda': latest.get('EV/EBITDA'),
        'pb': latest.get('P/B'),
        'total_quarters': len(ticker_data)
    }

    return info


def clear_cache():
    """
    Limpa o cache de dados.
    """
    st.cache_data.clear()
