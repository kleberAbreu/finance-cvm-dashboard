"""
Carregamento de dados Parquet com fallback para amostra publica.
"""
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Any, Dict, Tuple
from config.settings import (
    PARQUET_BASE_FILE, PARQUET_SETORES_FILE, PARQUET_MERCADO_FILE,
    SAMPLE_PARQUET_BASE_FILE, SAMPLE_PARQUET_SETORES_FILE,
    SAMPLE_PARQUET_MERCADO_FILE, CACHE_TTL
)
from src.utils.validators import validate_parquet_structure, check_data_quality


def get_default_data_paths() -> Dict[str, Path]:
    """Retorna os caminhos dos dados de producao gerados pelo pipeline."""
    return {
        'base': PARQUET_BASE_FILE,
        'setores': PARQUET_SETORES_FILE,
        'mercado': PARQUET_MERCADO_FILE,
    }


def get_sample_data_paths() -> Dict[str, Path]:
    """Retorna os caminhos dos dados de amostra versionados no repositorio."""
    return {
        'base': SAMPLE_PARQUET_BASE_FILE,
        'setores': SAMPLE_PARQUET_SETORES_FILE,
        'mercado': SAMPLE_PARQUET_MERCADO_FILE,
    }


def resolve_data_paths(
    base_file: Path = PARQUET_BASE_FILE,
    setores_file: Path = PARQUET_SETORES_FILE,
    mercado_file: Path = PARQUET_MERCADO_FILE
) -> Tuple[Dict[str, Path], bool, list[str]]:
    """
    Resolve quais arquivos Parquet devem ser usados.

    Prioriza os dados gerados pelo pipeline. Se eles nao existirem ou estiverem
    incompletos, usa a amostra publica para que um clone limpo rode localmente.
    """
    from src.publication import is_public_demo
    if is_public_demo():
        sample_paths = get_sample_data_paths()
        valid, errors = validate_parquet_structure(sample_paths)
        if not valid:
            raise ValueError(f"Amostra demonstrativa inválida: {errors}")
        return sample_paths, True, []

    requested_paths = {
        'base': Path(base_file),
        'setores': Path(setores_file),
        'mercado': Path(mercado_file),
    }
    requested_valid, requested_errors = validate_parquet_structure(requested_paths)
    if requested_valid:
        return requested_paths, False, []

    sample_paths = get_sample_data_paths()
    sample_valid, sample_errors = validate_parquet_structure(sample_paths)
    if sample_valid:
        return sample_paths, True, requested_errors

    all_errors = requested_errors + [f"Amostra publica invalida: {err}" for err in sample_errors]
    return requested_paths, False, all_errors


def get_data_source_info(
    base_file: Path = PARQUET_BASE_FILE,
    setores_file: Path = PARQUET_SETORES_FILE,
    mercado_file: Path = PARQUET_MERCADO_FILE
) -> Dict[str, Any]:
    """Retorna metadados simples sobre a fonte ativa de dados."""
    paths, using_sample, errors = resolve_data_paths(base_file, setores_file, mercado_file)
    return {
        'paths': paths,
        'using_sample': using_sample,
        'errors': errors,
        'label': 'Amostra publica' if using_sample else 'Dados do pipeline',
    }


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

    file_paths, using_sample, errors = resolve_data_paths(base_file, setores_file, mercado_file)
    if errors and not using_sample:
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
        # Ativo
        'Ativo Total', 'Ativo Circulante', 'Caixa', 'Aplicações Financeiras',
        'Contas a Receber', 'Estoques', 'Ativo Não Circulante',
        'Imobilizado', 'Intangível',
        # Passivo
        'Passivo Circulante', 'Passivo Não Circulante',
        'Dívida Bruta', 'Dívida Líquida', 'Patrimônio Líquido',
        # DRE
        'Receita Líquida', 'CPV', 'Lucro Bruto',
        'Despesas Operacionais', 'EBIT', 'Lucro Líquido', 'Resultado Financeiro',
        'IR', 'D&A', 'EBITDA',
        # DFC
        'FCO', 'FCI', 'FCF',
        # Mercado
        'Preço de Fechamento', 'Qtde Ações',
        'Market Cap', 'Enterprise Value', 'P/E', 'EV/EBITDA', 'P/B', 'DL/EV'
    ]

    for col in numeric_cols:
        if col in df_base.columns:
            df_base[col] = pd.to_numeric(df_base[col], errors='coerce')

    # Converter Qtde Ações de milhões para unidades (se necessário para cálculos)
    # Nota: a coluna vem em milhões no dataset gerado, mantemos compatibilidade.
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
