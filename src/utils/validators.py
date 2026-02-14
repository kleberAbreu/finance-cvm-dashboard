"""
Validação de estrutura e qualidade de dados.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from config.settings import SHEET_BASE, SHEET_SETORES, SHEET_MERCADO, COLS_BASE


def validate_excel_structure(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Valida estrutura básica do arquivo Excel.

    Args:
        file_path: Caminho do arquivo Excel

    Returns:
        Tuple (is_valid, list_of_errors)
    """
    errors = []

    # Verificar se arquivo existe
    if not file_path.exists():
        errors.append(f"Arquivo não encontrado: {file_path}")
        return False, errors

    try:
        # Carregar Excel
        xl = pd.ExcelFile(file_path)

        # Verificar planilhas esperadas
        expected_sheets = {SHEET_BASE, SHEET_SETORES, SHEET_MERCADO}
        found_sheets = set(xl.sheet_names)

        missing_sheets = expected_sheets - found_sheets
        if missing_sheets:
            errors.append(f"Planilhas faltando: {', '.join(missing_sheets)}")

        # Verificar colunas da Base Consolidada
        if SHEET_BASE in xl.sheet_names:
            df_base = pd.read_excel(file_path, sheet_name=SHEET_BASE, nrows=0)

            # Verificar apenas colunas essenciais (mais flexível)
            essential_cols = ['Ticker', 'Tipo', 'DT_FIM_EXERC', 'Market_Cap', 'EBITDA']
            found_cols = set(df_base.columns)

            missing_essential = set(essential_cols) - found_cols
            if missing_essential:
                errors.append(f"Colunas essenciais faltando em '{SHEET_BASE}': {', '.join(missing_essential)}")

    except Exception as e:
        errors.append(f"Erro ao ler Excel: {str(e)}")

    is_valid = len(errors) == 0
    return is_valid, errors


def check_data_quality(df: pd.DataFrame) -> Dict[str, any]:
    """
    Analisa qualidade dos dados de um DataFrame.

    Args:
        df: DataFrame para análise

    Returns:
        Dicionário com métricas de qualidade
    """
    total_cells = df.shape[0] * df.shape[1]

    quality_report = {
        'total_rows': df.shape[0],
        'total_cols': df.shape[1],
        'total_cells': total_cells,
        'missing_cells': df.isna().sum().sum(),
        'missing_percent': (df.isna().sum().sum() / total_cells * 100) if total_cells > 0 else 0,
        'columns_with_missing': df.columns[df.isna().any()].tolist(),
        'duplicated_rows': df.duplicated().sum()
    }

    # Verificar valores infinitos em colunas numéricas
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    inf_counts = {}
    for col in numeric_cols:
        inf_count = df[col].apply(lambda x: x == float('inf') or x == float('-inf')).sum()
        if inf_count > 0:
            inf_counts[col] = inf_count

    quality_report['infinite_values'] = inf_counts
    quality_report['infinite_total'] = sum(inf_counts.values())

    return quality_report


def detect_outliers(series: pd.Series, method: str = 'iqr', threshold: float = 1.5) -> pd.Series:
    """
    Detecta outliers em uma série numérica.

    Args:
        series: Série de dados
        method: Método de detecção ('iqr' ou 'zscore')
        threshold: Threshold para detecção (1.5 para IQR, 3 para zscore)

    Returns:
        Série booleana indicando outliers
    """
    # Remover NaN e infinitos
    clean_series = series.dropna()
    clean_series = clean_series[~clean_series.isin([float('inf'), float('-inf')])]

    if len(clean_series) == 0:
        return pd.Series([False] * len(series), index=series.index)

    if method == 'iqr':
        Q1 = clean_series.quantile(0.25)
        Q3 = clean_series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        outliers = (series < lower_bound) | (series > upper_bound)

    elif method == 'zscore':
        mean = clean_series.mean()
        std = clean_series.std()
        if std == 0:
            return pd.Series([False] * len(series), index=series.index)
        z_scores = (series - mean) / std
        outliers = z_scores.abs() > threshold

    else:
        raise ValueError(f"Método desconhecido: {method}")

    return outliers.fillna(False)


def validate_ticker_mapping(ticker_file: Path) -> Tuple[bool, List[str]]:
    """
    Valida arquivo de mapeamento de tickers.

    Args:
        ticker_file: Caminho do arquivo CSV

    Returns:
        Tuple (is_valid, list_of_errors)
    """
    errors = []

    if not ticker_file.exists():
        errors.append(f"Arquivo de tickers não encontrado: {ticker_file}")
        return False, errors

    try:
        # Tentar carregar com diferentes encodings
        for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
            try:
                df = pd.read_csv(ticker_file, sep=';', encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            errors.append("Não foi possível ler o arquivo com encodings padrão")
            return False, errors

        # Verificar colunas esperadas
        expected_cols = ['CNPJ', 'Nome', 'Ticker', 'Tipo']
        missing_cols = set(expected_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"Colunas faltando: {', '.join(missing_cols)}")

        # Verificar duplicatas
        if 'CNPJ' in df.columns:
            duplicated = df['CNPJ'].duplicated().sum()
            if duplicated > 0:
                errors.append(f"{duplicated} CNPJs duplicados encontrados")

        # Verificar valores vazios
        if df.isna().any().any():
            cols_with_na = df.columns[df.isna().any()].tolist()
            errors.append(f"Valores vazios encontrados em: {', '.join(cols_with_na)}")

    except Exception as e:
        errors.append(f"Erro ao validar arquivo de tickers: {str(e)}")

    is_valid = len(errors) == 0
    return is_valid, errors
