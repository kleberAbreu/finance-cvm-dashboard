"""
Página 1: Overview - Visão Geral do Mercado.
"""
import streamlit as st
import pandas as pd
from src.data.loader import load_and_prepare_base
from src.data.preprocessor import get_latest_quarter_data, aggregate_by_sector
from src.components.sidebar import render_sidebar_filters, apply_filters, render_export_buttons
from src.components.metrics_cards import render_market_summary
from src.components.charts import (
    create_pie_chart, create_sector_comparison_bar,
    create_time_series_chart
)
from config.settings import PARQUET_BASE_FILE

st.set_page_config(page_title="Overview - Dashboard CVM", page_icon="🌐", layout="wide")

st.title("🌐 Visão Geral do Mercado")

# Aplicar filtros
filters = render_sidebar_filters()

try:
    # Carregar dados
    df_base = load_and_prepare_base(PARQUET_BASE_FILE)
    df_filtered = apply_filters(df_base, filters)

    if len(df_filtered) == 0:
        st.warning("Nenhum dado disponível com os filtros aplicados")
        st.stop()

    # Hero Metrics
    st.header("📊 Métricas Principais")
    render_market_summary(df_filtered)

    st.divider()

    # Composição do mercado
    st.header("📈 Composição do Mercado")

    # Dados mais recentes
    df_latest = get_latest_quarter_data(df_filtered)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Market Cap por Setor")

        # Agregar por setor
        df_sector_agg = df_latest.groupby('Tipo').agg({
            'Market Cap': 'sum',
            'Ticker': 'nunique'
        }).reset_index()
        df_sector_agg = df_sector_agg.sort_values('Market Cap', ascending=False).head(10)

        fig_pie = create_pie_chart(
            df_sector_agg,
            values='Market Cap',
            names='Tipo',
            title="Top 10 Setores por Market Cap"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Número de Empresas por Setor")

        df_sector_count = df_latest.groupby('Tipo').agg({
            'Ticker': 'nunique'
        }).reset_index()
        df_sector_count.columns = ['Tipo', 'Qtde_Empresas']
        df_sector_count = df_sector_count.sort_values('Qtde_Empresas', ascending=False).head(10)

        fig_bar = create_sector_comparison_bar(
            df_sector_count,
            metric='Qtde_Empresas',
            title="Top 10 Setores por Número de Empresas",
            horizontal=True
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Evolução temporal
    st.header("📉 Evolução Temporal")

    tab1, tab2, tab3 = st.tabs(["Market Cap Total", "P/E Mediano", "EV/EBITDA Mediano"])

    with tab1:
        # Agregar Market Cap por trimestre
        df_time = df_filtered.groupby('Data_Trimestre').agg({
            'Market Cap': 'sum',
            'Ticker': 'nunique'
        }).reset_index()

        fig_mc = create_time_series_chart(
            df_time,
            metric='Market Cap',
            companies=['Total'],
            date_col='Data_Trimestre',
            ticker_col='Ticker',
            title="Evolução do Market Cap Total"
        )

        # Criar gráfico simples já que não temos múltiplas empresas
        import plotly.graph_objects as go
        fig_mc = go.Figure()
        fig_mc.add_trace(go.Scatter(
            x=df_time['Data_Trimestre'],
            y=df_time['Market Cap'],
            mode='lines+markers',
            name='Market Cap Total',
            line=dict(color='steelblue', width=3)
        ))
        fig_mc.update_layout(
            title="Evolução do Market Cap Total",
            xaxis_title="Data",
            yaxis_title="Market Cap (R$)",
            hovermode='x unified',
            template='plotly_white'
        )

        st.plotly_chart(fig_mc, use_container_width=True)

    with tab2:
        # P/E mediano ao longo do tempo
        df_time_pe = df_filtered.replace([float('inf'), float('-inf')], float('nan'))
        df_time_pe = df_time_pe.groupby('Data_Trimestre')['P/E'].median().reset_index()

        import plotly.graph_objects as go
        fig_pe = go.Figure()
        fig_pe.add_trace(go.Scatter(
            x=df_time_pe['Data_Trimestre'],
            y=df_time_pe['P/E'],
            mode='lines+markers',
            name='P/E Mediano',
            line=dict(color='orange', width=3)
        ))
        fig_pe.update_layout(
            title="Evolução do P/E Mediano",
            xaxis_title="Data",
            yaxis_title="P/E",
            hovermode='x unified',
            template='plotly_white'
        )

        st.plotly_chart(fig_pe, use_container_width=True)

    with tab3:
        # EV/EBITDA mediano ao longo do tempo
        df_time_ev = df_filtered.replace([float('inf'), float('-inf')], float('nan'))
        df_time_ev = df_time_ev.groupby('Data_Trimestre')['EV/EBITDA'].median().reset_index()

        import plotly.graph_objects as go
        fig_ev = go.Figure()
        fig_ev.add_trace(go.Scatter(
            x=df_time_ev['Data_Trimestre'],
            y=df_time_ev['EV/EBITDA'],
            mode='lines+markers',
            name='EV/EBITDA Mediano',
            line=dict(color='green', width=3)
        ))
        fig_ev.update_layout(
            title="Evolução do EV/EBITDA Mediano",
            xaxis_title="Data",
            yaxis_title="EV/EBITDA",
            hovermode='x unified',
            template='plotly_white'
        )

        st.plotly_chart(fig_ev, use_container_width=True)

    st.divider()

    # Top movers
    st.header("🏆 Rankings")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 - Maiores por Market Cap")

        df_top_mc = df_latest.sort_values('Market Cap', ascending=False).head(10)
        df_display = df_top_mc[['Ticker', 'Empresa', 'Tipo', 'Market Cap', 'P/E', 'EV/EBITDA']].copy()

        # Formatar valores
        from src.utils.formatters import format_currency, format_multiple
        df_display['Market Cap'] = df_display['Market Cap'].apply(format_currency)
        df_display['P/E'] = df_display['P/E'].apply(format_multiple)
        df_display['EV/EBITDA'] = df_display['EV/EBITDA'].apply(format_multiple)

        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Top 10 - Maiores EBITDA")

        df_top_ebitda = df_latest.sort_values('EBITDA', ascending=False).head(10)
        df_display = df_top_ebitda[['Ticker', 'Empresa', 'Tipo', 'EBITDA', 'P/E', 'EV/EBITDA']].copy()

        # Formatar valores
        df_display['EBITDA'] = df_display['EBITDA'].apply(format_currency)
        df_display['P/E'] = df_display['P/E'].apply(format_multiple)
        df_display['EV/EBITDA'] = df_display['EV/EBITDA'].apply(format_multiple)

        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Renderizar botões de exportação
    render_export_buttons(df_filtered)

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(traceback.format_exc())
