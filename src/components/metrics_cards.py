"""
Componentes de cards de métricas/KPIs.
"""
import streamlit as st
import pandas as pd
from typing import Optional
from src.utils.formatters import format_currency, format_currency_compact, format_number, format_percent, format_multiple


def render_kpi_card(title: str, value: float, delta: Optional[float] = None,
                   format_type: str = 'currency', help_text: Optional[str] = None):
    """
    Renderiza um card de KPI.

    Args:
        title: Título do KPI
        value: Valor principal
        delta: Valor de variação/comparação
        format_type: Tipo de formatação ('currency', 'number', 'percent', 'multiple')
        help_text: Texto de ajuda (tooltip)
    """
    # Formatar valor
    if format_type == 'currency':
        formatted_value = format_currency_compact(value)
    elif format_type == 'integer':
        formatted_value = str(int(value))
    elif format_type == 'number':
        formatted_value = format_number(value)
    elif format_type == 'percent':
        formatted_value = format_percent(value, include_sign=False)
    elif format_type == 'multiple':
        formatted_value = format_multiple(value)
    else:
        formatted_value = str(value)

    # Formatar delta
    if delta is not None:
        if format_type == 'currency':
            delta_formatted = format_currency_compact(delta)
        elif format_type == 'percent':
            delta_formatted = format_percent(delta)
        else:
            delta_formatted = format_number(delta)

        st.metric(
            label=title,
            value=formatted_value,
            delta=delta_formatted,
            help=help_text
        )
    else:
        st.metric(
            label=title,
            value=formatted_value,
            help=help_text
        )


def render_market_summary(df: pd.DataFrame):
    """
    Renderiza resumo do mercado com 4 KPIs principais.

    Args:
        df: DataFrame com dados consolidados (filtrados)
    """
    # Calcular métricas
    if len(df) == 0:
        st.warning("Nenhum dado disponível para exibir")
        return

    # Pegar dados mais recentes por empresa
    df_latest = df.sort_values('Data_Trimestre').groupby('Ticker').tail(1)

    total_market_cap = df_latest['Market Cap'].sum()
    num_companies = df_latest['Ticker'].nunique()

    # Medianas de múltiplos (remover inf/NaN)
    df_clean = df_latest.replace([float('inf'), float('-inf')], float('nan'))
    median_pe = df_clean['P/E'].median()
    median_ev_ebitda = df_clean['EV/EBITDA'].median()

    # Renderizar cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Market Cap Total",
            total_market_cap,
            format_type='currency',
            help_text="Soma do Market Cap de todas as empresas"
        )

    with col2:
        render_kpi_card(
            "Empresas",
            num_companies,
            format_type='integer',
            help_text="Número de empresas no dataset filtrado"
        )

    with col3:
        render_kpi_card(
            "P/E Mediano",
            median_pe,
            format_type='multiple',
            help_text="Mediana do múltiplo Preço/Lucro"
        )

    with col4:
        render_kpi_card(
            "EV/EBITDA Mediano",
            median_ev_ebitda,
            format_type='multiple',
            help_text="Mediana do múltiplo Enterprise Value/EBITDA"
        )


def render_company_profile_card(ticker: str, df: pd.DataFrame):
    """
    Renderiza card de perfil de uma empresa.

    Args:
        ticker: Código do ticker
        df: DataFrame com dados da empresa
    """
    if len(df) == 0:
        st.warning(f"Nenhum dado disponível para {ticker}")
        return

    # Pegar dados mais recentes
    latest = df.sort_values('Data_Trimestre').iloc[-1]

    st.subheader(f"{latest.get('Empresa', ticker)}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Ticker:** {ticker}")
        st.markdown(f"**Setor:** {latest.get('Tipo', 'N/A')}")

    with col2:
        st.markdown(f"**Market Cap:** {format_currency(latest.get('Market Cap'))}")
        st.markdown(f"**P/E:** {format_multiple(latest.get('P/E'))}")

    # Métricas adicionais
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "EV/EBITDA",
            latest.get('EV/EBITDA'),
            format_type='multiple'
        )

    with col2:
        render_kpi_card(
            "P/B",
            latest.get('P/B'),
            format_type='multiple'
        )

    with col3:
        render_kpi_card(
            "Patrimônio Líquido",
            latest.get('Patrimônio Líquido'),
            format_type='currency'
        )

    with col4:
        render_kpi_card(
            "Dívida Líquida",
            latest.get('Dívida Líquida'),
            format_type='currency'
        )


def render_sector_comparison_summary(df_setores: pd.DataFrame, selected_sectors: list):
    """
    Renderiza resumo de comparação setorial.

    Args:
        df_setores: DataFrame de resumo setorial
        selected_sectors: Lista de setores selecionados
    """
    if len(selected_sectors) == 0:
        st.info("Selecione setores para comparar")
        return

    df_filtered = df_setores[df_setores['Tipo'].isin(selected_sectors)]

    if len(df_filtered) == 0:
        st.warning("Nenhum dado disponível para os setores selecionados")
        return

    st.subheader(f"Comparando {len(selected_sectors)} setores")

    # Métricas agregadas
    col1, col2, col3 = st.columns(3)

    with col1:
        total_companies = df_filtered['Qtde_Empresas'].sum()
        render_kpi_card(
            "Total de Empresas",
            total_companies,
            format_type='integer'
        )

    with col2:
        avg_pe = df_filtered['Mediana_PE'].median()
        render_kpi_card(
            "P/E Mediano",
            avg_pe,
            format_type='multiple'
        )

    with col3:
        avg_ev_ebitda = df_filtered['Mediana_EV_EBITDA'].median()
        render_kpi_card(
            "EV/EBITDA Mediano",
            avg_ev_ebitda,
            format_type='multiple'
        )


def render_stats_summary(series: pd.Series, title: str = "Estatísticas"):
    """
    Renderiza resumo estatístico de uma série.

    Args:
        series: Série de dados
        title: Título da seção
    """
    st.subheader(title)

    # Limpar dados
    clean_series = series.dropna()
    clean_series = clean_series[~clean_series.isin([float('inf'), float('-inf')])]

    if len(clean_series) == 0:
        st.warning("Nenhum dado válido disponível")
        return

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Mínimo", f"{clean_series.min():.2f}")

    with col2:
        st.metric("Q1", f"{clean_series.quantile(0.25):.2f}")

    with col3:
        st.metric("Mediana", f"{clean_series.median():.2f}")

    with col4:
        st.metric("Q3", f"{clean_series.quantile(0.75):.2f}")

    with col5:
        st.metric("Máximo", f"{clean_series.max():.2f}")
