"""
Funções de formatação de números, datas e valores monetários.
"""
import pandas as pd
import numpy as np
from typing import Union
from config.settings import CURRENCY_SCALE


def format_currency(value: Union[float, int, None], prefix: str = "R$ ") -> str:
    """
    Formata valor monetário em formato brasileiro com escala (tri, bi, mi, mil).

    Args:
        value: Valor numérico
        prefix: Prefixo monetário (padrão "R$ ")

    Returns:
        String formatada (ex: "R$ 1,2 tri")
    """
    if value is None or pd.isna(value) or np.isinf(value):
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    # Determinar escala
    for scale, suffix in sorted(CURRENCY_SCALE.items(), reverse=True):
        if abs_value >= scale:
            scaled = abs_value / scale
            return f"{sign}{prefix}{scaled:,.1f} {suffix}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Valores menores que mil
    return f"{sign}{prefix}{abs_value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: Union[float, int, None], decimals: int = 1) -> str:
    """
    Formata número grande com sufixos (M, K).

    Args:
        value: Valor numérico
        decimals: Casas decimais

    Returns:
        String formatada (ex: "1,2M")
    """
    if value is None or pd.isna(value) or np.isinf(value):
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1e9:
        return f"{sign}{abs_value/1e9:.{decimals}f}B".replace(".", ",")
    elif abs_value >= 1e6:
        return f"{sign}{abs_value/1e6:.{decimals}f}M".replace(".", ",")
    elif abs_value >= 1e3:
        return f"{sign}{abs_value/1e3:.{decimals}f}K".replace(".", ",")
    else:
        return f"{sign}{abs_value:.{decimals}f}".replace(".", ",")


def format_percent(value: Union[float, None], decimals: int = 1, include_sign: bool = True) -> str:
    """
    Formata percentual.

    Args:
        value: Valor decimal (0.125 = 12,5%)
        decimals: Casas decimais
        include_sign: Incluir sinal de + para positivos

    Returns:
        String formatada (ex: "+12,5%")
    """
    if value is None or pd.isna(value) or np.isinf(value):
        return "N/A"

    pct = value * 100
    sign = "+" if pct > 0 and include_sign else ""
    return f"{sign}{pct:.{decimals}f}%".replace(".", ",")


def format_multiple(value: Union[float, None], decimals: int = 2) -> str:
    """
    Formata múltiplos de valuation (P/E, EV/EBITDA).

    Args:
        value: Valor do múltiplo
        decimals: Casas decimais

    Returns:
        String formatada (ex: "12,5x")
    """
    if value is None or pd.isna(value) or np.isinf(value):
        return "N/A"

    return f"{value:.{decimals}f}x".replace(".", ",")


def format_date(date: pd.Timestamp, format_type: str = 'quarter') -> str:
    """
    Formata data para exibição.

    Args:
        date: Data como Timestamp
        format_type: Tipo de formatação ('quarter', 'full', 'short')

    Returns:
        String formatada (ex: "Q3 2025")
    """
    if pd.isna(date):
        return "N/A"

    if format_type == 'quarter':
        quarter = (date.month - 1) // 3 + 1
        return f"Q{quarter} {date.year}"
    elif format_type == 'full':
        return date.strftime('%d/%m/%Y')
    elif format_type == 'short':
        return date.strftime('%m/%Y')
    else:
        return str(date)


def format_trimestre(trimestre: str) -> str:
    """
    Converte formato de trimestre interno para exibição.

    Args:
        trimestre: String no formato "2025Q3"

    Returns:
        String formatada "Q3 2025"
    """
    if not trimestre or pd.isna(trimestre):
        return "N/A"

    try:
        year = trimestre[:4]
        quarter = trimestre[-2:]
        return f"{quarter} {year}"
    except:
        return str(trimestre)


def color_negative_red(val: Union[float, str]) -> str:
    """
    Retorna CSS para colorir valores negativos de vermelho (para DataFrame.style).

    Args:
        val: Valor da célula

    Returns:
        String CSS
    """
    if isinstance(val, (int, float)):
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'
    return ''


def color_scale_red_green(val: Union[float, None], vmin: float, vmax: float) -> str:
    """
    Retorna CSS com escala de cor vermelho-amarelo-verde baseada no valor.

    Args:
        val: Valor da célula
        vmin: Valor mínimo da escala
        vmax: Valor máximo da escala

    Returns:
        String CSS
    """
    if val is None or pd.isna(val) or np.isinf(val):
        return ''

    # Normalizar entre 0 e 1
    normalized = (val - vmin) / (vmax - vmin) if vmax != vmin else 0.5
    normalized = max(0, min(1, normalized))  # Clip entre 0 e 1

    if normalized < 0.5:
        # Vermelho para amarelo
        r = 255
        g = int(255 * (normalized * 2))
        b = 0
    else:
        # Amarelo para verde
        r = int(255 * (2 - normalized * 2))
        g = 255
        b = 0

    return f'background-color: rgb({r},{g},{b})'
