"""
Página 3: Sector Comparison - Comparação Setorial.
"""
import streamlit as st
import pandas as pd
from src.data.loader import load_and_prepare_base, get_available_sectors
from src.data.preprocessor import get_latest_quarter_data, filter_by_sectors
from src.components.sidebar import render_sidebar_filters, apply_filters
from src.components.metrics_cards import render_sector_comparison_summary
from src.components.charts import (
    create_sector_comparison_bar, create_scatter_matrix,
    create_distribution_plot
)
from config.settings import DEFAULT_EXCEL

st.set_page_config(page_title="Sector Comparison - Dashboard CVM", page_icon="🏭", layout="wide")

st.title("🏭 Comparação Setorial")

# Aplicar filtros
filters = render_sidebar_filters()

try:
    # Carregar dados
    df_base = load_and_prepare_base(DEFAULT_EXCEL)
    all_sectors = get_available_sectors(DEFAULT_EXCEL)

    # Seleção de setores
    st.header("📌 Selecione Setores para Comparar")

    selected_sectors = st.multiselect(
        f"Escolha até 10 setores ({len(all_sectors)} disponíveis):",
        options=all_sectors,
        default=all_sectors[:5] if len(all_sectors) >= 5 else all_sectors,
        max_selections=10,
        key='selected_sectors'
    )

    if not selected_sectors:
        st.warning("Selecione pelo menos um setor para análise")
        st.stop()

    # Filtrar dados
    df_filtered = filter_by_sectors(df_base, selected_sectors)
    df_latest = get_latest_quarter_data(df_filtered)

    # Agregação por setor
    from src.data.preprocessor import aggregate_by_sector

    df_sector_agg = df_latest.groupby('Tipo').agg({
        'Ticker': 'nunique',
        'Market Cap': 'sum',
        'P/E': 'median',
        'EV/EBITDA': 'median',
        'P/B': 'median',
        'DL/EV': 'median',
        'EBITDA': 'sum'
    }).reset_index()

    df_sector_agg.columns = [
        'Tipo', 'Qtde_Empresas', 'Market_Cap_Total',
        'Mediana_PE', 'Mediana_EV_EBITDA', 'Mediana_PB',
        'Mediana_DL_EV', 'EBITDA_Total'
    ]

    # Resumo
    render_sector_comparison_summary(df_sector_agg, selected_sectors)

    st.divider()

    # Tabela agregada
    st.header("📊 Tabela Comparativa")

    # Formatar tabela
    df_display = df_sector_agg.copy()

    from src.utils.formatters import format_currency, format_multiple

    df_display['Market_Cap_Total'] = df_display['Market_Cap_Total'].apply(format_currency)
    df_display['EBITDA_Total'] = df_display['EBITDA_Total'].apply(format_currency)
    df_display['Mediana_PE'] = df_display['Mediana_PE'].apply(format_multiple)
    df_display['Mediana_EV_EBITDA'] = df_display['Mediana_EV_EBITDA'].apply(format_multiple)
    df_display['Mediana_PB'] = df_display['Mediana_PB'].apply(format_multiple)
    df_display['Mediana_DL_EV'] = df_display['Mediana_DL_EV'].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tipo": "Setor",
            "Qtde_Empresas": "# Empresas",
            "Market_Cap_Total": "Market Cap Total",
            "Mediana_PE": "P/E Mediano",
            "Mediana_EV_EBITDA": "EV/EBITDA Mediano",
            "Mediana_PB": "P/B Mediano",
            "Mediana_DL_EV": "DL/EV Mediano",
            "EBITDA_Total": "EBITDA Total"
        }
    )

    st.divider()

    # Visualizações
    st.header("📈 Visualizações")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Gráficos de Barras",
        "Bubble Chart",
        "Séries Temporais",
        "Box Plots"
    ])

    with tab1:
        st.subheader("Comparação por Métrica")

        col1, col2 = st.columns(2)

        with col1:
            metric1 = st.selectbox(
                "Métrica 1:",
                options=['Market_Cap_Total', 'Mediana_PE', 'Mediana_EV_EBITDA', 'Mediana_PB', 'EBITDA_Total'],
                index=0,
                key='metric1'
            )

        with col2:
            metric2 = st.selectbox(
                "Métrica 2:",
                options=['Market_Cap_Total', 'Mediana_PE', 'Mediana_EV_EBITDA', 'Mediana_PB', 'EBITDA_Total'],
                index=1,
                key='metric2'
            )

        col1, col2 = st.columns(2)

        with col1:
            fig1 = create_sector_comparison_bar(
                df_sector_agg,
                metric=metric1,
                title=f"{metric1} por Setor"
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = create_sector_comparison_bar(
                df_sector_agg,
                metric=metric2,
                title=f"{metric2} por Setor"
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Análise de Dispersão")

        col1, col2, col3 = st.columns(3)

        with col1:
            x_metric = st.selectbox(
                "Eixo X:",
                options=['P/E', 'EV/EBITDA', 'P/B', 'DL/EV'],
                index=0,
                key='bubble_x'
            )

        with col2:
            y_metric = st.selectbox(
                "Eixo Y:",
                options=['P/E', 'EV/EBITDA', 'P/B', 'DL/EV'],
                index=1,
                key='bubble_y'
            )

        with col3:
            size_metric = st.selectbox(
                "Tamanho:",
                options=['Market Cap', 'EBITDA', 'Ativo Total'],
                index=0,
                key='bubble_size'
            )

        fig_scatter = create_scatter_matrix(
            df_latest,
            x=x_metric,
            y=y_metric,
            color_by='Tipo',
            size_by=size_metric,
            title=f"{y_metric} vs {x_metric} (tamanho = {size_metric})"
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("Evolução Temporal de Medianas Setoriais")

        metric_ts = st.selectbox(
            "Selecione métrica:",
            options=['P/E', 'EV/EBITDA', 'P/B', 'Market Cap'],
            key='ts_metric'
        )

        # Calcular medianas ao longo do tempo
        df_time_sector = df_filtered.groupby(['Data_Trimestre', 'Tipo'])[metric_ts].median().reset_index()

        # Criar gráfico
        import plotly.express as px

        fig_ts = px.line(
            df_time_sector,
            x='Data_Trimestre',
            y=metric_ts,
            color='Tipo',
            title=f"Evolução de {metric_ts} Mediano por Setor",
            template='plotly_white'
        )

        fig_ts.update_layout(
            xaxis_title="Data",
            yaxis_title=metric_ts,
            hovermode='x unified'
        )

        st.plotly_chart(fig_ts, use_container_width=True)

    with tab4:
        st.subheader("Distribuição de Múltiplos por Setor")

        box_metric = st.selectbox(
            "Selecione métrica:",
            options=['P/E', 'EV/EBITDA', 'P/B', 'DL/EV'],
            key='box_metric'
        )

        fig_box = create_distribution_plot(
            df_latest,
            metric=box_metric,
            group_by='Tipo',
            title=f"Distribuição de {box_metric} por Setor"
        )

        st.plotly_chart(fig_box, use_container_width=True)

    st.divider()

    # Deep-dive por setor
    st.header("🔍 Deep-Dive por Setor")

    sector_detail = st.selectbox(
        "Selecione setor para detalhamento:",
        options=selected_sectors,
        key='sector_detail'
    )

    if sector_detail:
        df_sector_detail = df_latest[df_latest['Tipo'] == sector_detail]

        st.subheader(f"Top 10 Empresas - {sector_detail}")

        df_top = df_sector_detail.sort_values('Market Cap', ascending=False).head(10)

        cols_display = ['Ticker', 'Empresa', 'Market Cap', 'P/E', 'EV/EBITDA', 'P/B', 'EBITDA']
        df_table = df_top[cols_display].copy()

        df_table['Market Cap'] = df_table['Market Cap'].apply(format_currency)
        df_table['EBITDA'] = df_table['EBITDA'].apply(format_currency)
        df_table['P/E'] = df_table['P/E'].apply(format_multiple)
        df_table['EV/EBITDA'] = df_table['EV/EBITDA'].apply(format_multiple)
        df_table['P/B'] = df_table['P/B'].apply(format_multiple)

        st.dataframe(df_table, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(traceback.format_exc())
