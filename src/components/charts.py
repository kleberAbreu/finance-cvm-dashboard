"""
Componentes de gráficos reutilizáveis com Plotly.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Optional
from config.settings import PLOTLY_TEMPLATE, COLOR_PALETTE
from src.utils.formatters import format_currency, format_multiple


def create_time_series_chart(df: pd.DataFrame, metric: str, companies: List[str],
                             date_col: str = 'Data_Trimestre',
                             ticker_col: str = 'Ticker',
                             title: Optional[str] = None) -> go.Figure:
    """
    Cria gráfico de série temporal para múltiplas empresas.

    Args:
        df: DataFrame com dados
        metric: Nome da métrica
        companies: Lista de tickers
        date_col: Nome da coluna de data
        ticker_col: Nome da coluna de ticker
        title: Título do gráfico

    Returns:
        Figura Plotly
    """
    if title is None:
        title = f"Evolução de {metric}"

    fig = go.Figure()

    for i, company in enumerate(companies):
        df_company = df[df[ticker_col] == company].sort_values(date_col)

        if len(df_company) == 0:
            continue

        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]

        fig.add_trace(go.Scatter(
            x=df_company[date_col],
            y=df_company[metric],
            name=company,
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate=f'<b>{company}</b><br>' +
                         f'{metric}: %{{y:,.2f}}<br>' +
                         'Data: %{x|%Y-%m-%d}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Data",
        yaxis_title=metric,
        template=PLOTLY_TEMPLATE,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_sector_comparison_bar(df: pd.DataFrame, metric: str,
                                 sector_col: str = 'Tipo',
                                 title: Optional[str] = None,
                                 horizontal: bool = True) -> go.Figure:
    """
    Cria gráfico de barras de comparação setorial.

    Args:
        df: DataFrame agregado por setor
        metric: Nome da métrica
        sector_col: Nome da coluna de setor
        title: Título do gráfico
        horizontal: Se True, barras horizontais

    Returns:
        Figura Plotly
    """
    if title is None:
        title = f"{metric} por Setor"

    df_sorted = df.sort_values(metric, ascending=True)

    if horizontal:
        fig = go.Figure(go.Bar(
            x=df_sorted[metric],
            y=df_sorted[sector_col],
            orientation='h',
            marker=dict(
                color=df_sorted[metric],
                colorscale='Viridis',
                showscale=True
            ),
            text=df_sorted[metric].apply(lambda x: f'{x:.2f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>' +
                         f'{metric}: %{{x:,.2f}}<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            xaxis_title=metric,
            yaxis_title="Setor",
            template=PLOTLY_TEMPLATE
        )
    else:
        fig = go.Figure(go.Bar(
            x=df_sorted[sector_col],
            y=df_sorted[metric],
            marker=dict(
                color=df_sorted[metric],
                colorscale='Viridis',
                showscale=True
            ),
            text=df_sorted[metric].apply(lambda x: f'{x:.2f}'),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>' +
                         f'{metric}: %{{y:,.2f}}<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            xaxis_title="Setor",
            yaxis_title=metric,
            template=PLOTLY_TEMPLATE,
            xaxis_tickangle=-45
        )

    return fig


def create_scatter_matrix(df: pd.DataFrame, x: str, y: str,
                         color_by: str = 'Tipo',
                         size_by: Optional[str] = 'Market Cap',
                         title: Optional[str] = None) -> go.Figure:
    """
    Cria scatter plot com cores e tamanhos.

    Args:
        df: DataFrame
        x: Métrica do eixo X
        y: Métrica do eixo Y
        color_by: Coluna para cor
        size_by: Coluna para tamanho das bolhas
        title: Título do gráfico

    Returns:
        Figura Plotly
    """
    # VALIDAÇÃO: Se X e Y são iguais, retornar aviso
    if x == y:
        fig = go.Figure()
        fig.add_annotation(
            text=f"⚠️ Correlação de {x} consigo mesmo não é significativa<br><br>Selecione métricas diferentes para análise de correlação",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="orange")
        )
        fig.update_layout(
            title=f"⚠️ Aviso: {x} vs {x}",
            template=PLOTLY_TEMPLATE,
            height=400
        )
        return fig

    if title is None:
        title = f"{y} vs {x}"

    # Preparar lista de colunas necessárias (sem duplicatas)
    columns_needed = list(set([x, y, color_by]))
    if size_by and size_by in df.columns:
        columns_needed.append(size_by)

    # Validar que todas as colunas existem
    missing_cols = [col for col in columns_needed if col not in df.columns]
    if missing_cols:
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ Colunas não encontradas: {', '.join(missing_cols)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

    # Limpar dados - copiar apenas colunas necessárias
    df_clean = df[columns_needed].copy()
    df_clean = df_clean.replace([np.inf, -np.inf], np.nan).dropna()

    if len(df_clean) == 0:
        return go.Figure().add_annotation(
            text="Nenhum dado válido disponível",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

    # Limpar caracteres problemáticos na coluna de cor
    if color_by in df_clean.columns:
        df_clean[color_by] = df_clean[color_by].astype(str).apply(
            lambda x: x.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
        )

    # Preparar parâmetros para scatter plot
    scatter_params = {
        'data_frame': df_clean,
        'x': x,
        'y': y,
        'title': title,
        'template': PLOTLY_TEMPLATE
    }

    # Adicionar cor se disponível
    if color_by in df_clean.columns:
        scatter_params['color'] = color_by
        scatter_params['hover_data'] = [color_by]

    # Adicionar tamanho se disponível e válido
    if size_by and size_by in df_clean.columns:
        scatter_params['size'] = size_by

    # Criar scatter
    try:
        fig = px.scatter(**scatter_params)
    except (KeyError, ValueError, TypeError) as e:
        # Fallback: criar scatter básico sem cor/tamanho
        try:
            fig = px.scatter(
                df_clean,
                x=x,
                y=y,
                title=title,
                template=PLOTLY_TEMPLATE
            )
        except Exception as e2:
            # Última tentativa: gráfico vazio com mensagem de erro
            fig = go.Figure()
            fig.add_annotation(
                text=f"❌ Erro ao criar gráfico: {str(e2)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color="red")
            )
            return fig

    # Adicionar linha de regressão
    from src.utils.calculations import calculate_regression_stats
    stats = calculate_regression_stats(df_clean[x], df_clean[y])

    if not np.isnan(stats['slope']):
        x_range = np.array([df_clean[x].min(), df_clean[x].max()])
        y_pred = stats['slope'] * x_range + stats['intercept']

        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_pred,
            mode='lines',
            name=f'Regressão (R²={stats["r_squared"]:.3f})',
            line=dict(color='red', dash='dash')
        ))

    fig.update_layout(
        xaxis_title=x,
        yaxis_title=y
    )

    return fig


def create_heatmap(df: pd.DataFrame, metrics: List[str],
                  title: str = "Matriz de Correlação") -> go.Figure:
    """
    Cria heatmap de correlação.

    Args:
        df: DataFrame
        metrics: Lista de métricas
        title: Título do gráfico

    Returns:
        Figura Plotly
    """
    from src.utils.calculations import calculate_correlation_matrix

    corr_matrix = calculate_correlation_matrix(df, metrics)

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlação")
    ))

    fig.update_layout(
        title=title,
        template=PLOTLY_TEMPLATE,
        xaxis_tickangle=-45
    )

    return fig


def create_distribution_plot(df: pd.DataFrame, metric: str,
                            group_by: Optional[str] = None,
                            title: Optional[str] = None) -> go.Figure:
    """
    Cria gráfico de distribuição (histograma ou box plot).

    Args:
        df: DataFrame
        metric: Métrica
        group_by: Coluna para agrupar (cria box plots)
        title: Título do gráfico

    Returns:
        Figura Plotly
    """
    if title is None:
        title = f"Distribuição de {metric}"

    # Limpar dados
    df_clean = df[[metric]].copy()
    if group_by:
        df_clean[group_by] = df[group_by]

    df_clean = df_clean.replace([np.inf, -np.inf], np.nan).dropna()

    if group_by:
        # Box plots por grupo
        fig = go.Figure()

        for group in df_clean[group_by].unique():
            df_group = df_clean[df_clean[group_by] == group]

            fig.add_trace(go.Box(
                y=df_group[metric],
                name=str(group),
                boxmean='sd'
            ))

        fig.update_layout(
            title=title,
            yaxis_title=metric,
            template=PLOTLY_TEMPLATE
        )
    else:
        # Histograma simples
        fig = go.Figure(go.Histogram(
            x=df_clean[metric],
            nbinsx=30,
            marker=dict(color='steelblue')
        ))

        fig.update_layout(
            title=title,
            xaxis_title=metric,
            yaxis_title="Frequência",
            template=PLOTLY_TEMPLATE
        )

    return fig


def create_pie_chart(df: pd.DataFrame, values: str, names: str,
                    title: Optional[str] = None) -> go.Figure:
    """
    Cria gráfico de pizza.

    Args:
        df: DataFrame
        values: Coluna de valores
        names: Coluna de nomes
        title: Título do gráfico

    Returns:
        Figura Plotly
    """
    if title is None:
        title = f"Distribuição de {values}"

    fig = go.Figure(data=[go.Pie(
        labels=df[names],
        values=df[values],
        hole=0.3,
        textposition='auto',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>' +
                     f'{values}: %{{value:,.0f}}<br>' +
                     'Percentual: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title=title,
        template=PLOTLY_TEMPLATE
    )

    return fig


def create_waterfall_chart(categories: List[str], values: List[float],
                          title: str = "Análise de Composição") -> go.Figure:
    """
    Cria gráfico waterfall.

    Args:
        categories: Lista de categorias
        values: Lista de valores
        title: Título do gráfico

    Returns:
        Figura Plotly
    """
    fig = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        measure=["relative"] * (len(categories) - 1) + ["total"],
        x=categories,
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
        title=title,
        template=PLOTLY_TEMPLATE,
        showlegend=False
    )

    return fig


def create_gauge_chart(value: float, min_val: float, max_val: float,
                      title: str = "Indicador",
                      thresholds: Optional[dict] = None) -> go.Figure:
    """
    Cria gráfico de gauge (velocímetro).

    Args:
        value: Valor atual
        min_val: Valor mínimo
        max_val: Valor máximo
        title: Título do gráfico
        thresholds: Dict com ranges {'low': 30, 'medium': 70, 'high': 100}

    Returns:
        Figura Plotly
    """
    if thresholds is None:
        thresholds = {'low': 33, 'medium': 66, 'high': 100}

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_val, thresholds['low']], 'color': "lightcoral"},
                {'range': [thresholds['low'], thresholds['medium']], 'color': "lightyellow"},
                {'range': [thresholds['medium'], max_val], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    fig.update_layout(template=PLOTLY_TEMPLATE)

    return fig


def create_area_chart(df: pd.DataFrame, date_col: str, metrics: List[str],
                     title: Optional[str] = None, stacked: bool = False) -> go.Figure:
    """
    Cria gráfico de área.

    Args:
        df: DataFrame
        date_col: Coluna de data
        metrics: Lista de métricas
        title: Título do gráfico
        stacked: Se True, áreas empilhadas

    Returns:
        Figura Plotly
    """
    if title is None:
        title = "Evolução Temporal"

    fig = go.Figure()

    for i, metric in enumerate(metrics):
        if metric not in df.columns:
            continue

        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]

        fig.add_trace(go.Scatter(
            x=df[date_col],
            y=df[metric],
            name=metric,
            mode='lines',
            line=dict(color=color, width=0),
            fill='tonexty' if stacked and i > 0 else 'tozeroy',
            stackgroup='one' if stacked else None
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Data",
        yaxis_title="Valor",
        template=PLOTLY_TEMPLATE,
        hovermode='x unified'
    )

    return fig
