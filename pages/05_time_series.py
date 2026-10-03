"""
Página 5: Time Series Analysis - Análise de Tendências Temporais.
"""
import streamlit as st
import pandas as pd
from src.data.loader import load_and_prepare_base, get_available_tickers
from src.data.preprocessor import filter_by_tickers
from src.components.sidebar import render_sidebar_filters, apply_filters, render_export_buttons
from src.components.charts import create_time_series_chart, create_area_chart
from src.utils.calculations import calculate_cagr, calculate_volatility
from config.settings import PARQUET_BASE_FILE

if 'ts_period' not in st.session_state:
    st.session_state['ts_period'] = 'Tudo'

def set_period(period):
    st.session_state['ts_period'] = period

st.set_page_config(page_title="Time Series - Dashboard CVM", page_icon="📈", layout="wide")

st.title("📈 Análise de Séries Temporais")

# Aplicar filtros
filters = render_sidebar_filters()

try:
    # Carregar dados
    df_base = load_and_prepare_base(PARQUET_BASE_FILE)
    df_filtered = apply_filters(df_base, filters)

    all_tickers = get_available_tickers(PARQUET_BASE_FILE)

    if len(df_filtered) == 0:
        st.warning("Nenhum dado disponível com os filtros aplicados")
        st.stop()

    # Configuração do gráfico
    st.header("⚙️ Configuração do Gráfico")

    col1, col2, col3 = st.columns(3)

    with col1:
        metric = st.selectbox(
            "Métrica:",
            options=[
                'Market Cap', 'EBITDA', 'Lucro Líquido',
                'P/E', 'EV/EBITDA', 'P/B',
                'Patrimônio Líquido', 'Dívida Líquida'
            ],
            index=0,
            key='ts_metric'
        )

    with col2:
        chart_type = st.selectbox(
            "Tipo de gráfico:",
            options=['Linha', 'Área', 'Barras'],
            key='ts_chart_type'
        )

    with col3:
        normalization = st.selectbox(
            "Normalização:",
            options=['Nenhuma', 'Base 100', '% Mudança'],
            key='ts_normalization'
        )

    st.divider()

    # Seleção de empresas/agregação
    st.subheader("📊 Seleção de Dados")

    aggregation = st.radio(
        "Visualizar:",
        options=['Empresas individuais', 'Média setorial', 'Média de mercado'],
        horizontal=True,
        key='ts_aggregation'
    )

    if aggregation == 'Empresas individuais':
        selected_companies = st.multiselect(
            "Selecione até 10 empresas:",
            options=all_tickers,
            default=all_tickers[:5] if len(all_tickers) >= 5 else all_tickers,
            max_selections=10,
            key='ts_companies'
        )

        if not selected_companies:
            st.warning("Selecione pelo menos uma empresa")
            st.stop()

        df_plot = filter_by_tickers(df_filtered, selected_companies)

    elif aggregation == 'Média setorial':
        from src.data.loader import get_available_sectors
        all_sectors = get_available_sectors(PARQUET_BASE_FILE)

        selected_sectors = st.multiselect(
            "Selecione setores:",
            options=all_sectors,
            default=all_sectors[:3] if len(all_sectors) >= 3 else all_sectors,
            key='ts_sectors'
        )

        if not selected_sectors:
            st.warning("Selecione pelo menos um setor")
            st.stop()

        # Agregar por setor e data
        df_plot = df_filtered[df_filtered['Tipo'].isin(selected_sectors)]
        df_plot = df_plot.groupby(['Data_Trimestre', 'Tipo'])[metric].median().reset_index()
        df_plot = df_plot.rename(columns={'Tipo': 'Ticker'})  # Para compatibilidade

    else:  # Média de mercado
        df_plot = df_filtered.groupby('Data_Trimestre')[metric].median().reset_index()
        df_plot['Ticker'] = 'Mercado'

    # Filtrar por período selecionado
    if st.session_state['ts_period'] != 'Tudo' and not df_plot.empty:
        df_plot['Data_Trimestre'] = pd.to_datetime(df_plot['Data_Trimestre'])
        max_date = df_plot['Data_Trimestre'].max()
        if st.session_state['ts_period'] == '1 Ano':
            min_date = max_date - pd.DateOffset(years=1)
        elif st.session_state['ts_period'] == '3 Anos':
            min_date = max_date - pd.DateOffset(years=3)
        elif st.session_state['ts_period'] == '5 Anos':
            min_date = max_date - pd.DateOffset(years=5)
        elif st.session_state['ts_period'] == '10 Anos':
            min_date = max_date - pd.DateOffset(years=10)
        
        df_plot = df_plot[df_plot['Data_Trimestre'] >= min_date].copy()

    st.divider()

    # Aplicar normalização
    from src.utils.calculations import normalize_series

    if normalization != 'Nenhuma':
        if 'Ticker' in df_plot.columns:
            for ticker in df_plot['Ticker'].unique():
                mask = df_plot['Ticker'] == ticker
                series = df_plot.loc[mask, metric]

                if normalization == 'Base 100':
                    df_plot.loc[mask, metric] = normalize_series(series, method='base100')
                elif normalization == '% Mudança':
                    df_plot.loc[mask, metric] = normalize_series(series, method='pct_change')

    # Gráfico principal
    st.header("📊 Visualização")

    if aggregation == 'Empresas individuais':
        companies_to_plot = selected_companies
    elif aggregation == 'Média setorial':
        companies_to_plot = selected_sectors
    else:
        companies_to_plot = ['Mercado']

    if chart_type == 'Linha':
        fig = create_time_series_chart(
            df_plot,
            metric=metric,
            companies=companies_to_plot,
            title=f"Evolução de {metric}"
        )
    elif chart_type == 'Área':
        fig = create_area_chart(
            df_plot,
            date_col='Data_Trimestre',
            metrics=[metric],
            title=f"Evolução de {metric}",
            stacked=False
        )
    else:  # Barras
        import plotly.graph_objects as go

        fig = go.Figure()

        for company in companies_to_plot:
            df_company = df_plot[df_plot['Ticker'] == company]

            fig.add_trace(go.Bar(
                x=df_company['Data_Trimestre'],
                y=df_company[metric],
                name=company
            ))

        fig.update_layout(
            title=f"Evolução de {metric}",
            xaxis_title="Data",
            yaxis_title=metric,
            template='plotly_white',
            barmode='group',
            font=dict(family="Inter", size=12),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=50, b=10),
            hoverlabel=dict(bgcolor="#262730", font_size=13, font_family="Inter")
        )

    st.plotly_chart(fig, width='stretch')

    # Range selector (botões para filtrar período)
    st.subheader("⏱️ Período de Análise")

    col1, col2, col3, col4, col5 = st.columns(5)

    def get_btn_type(period):
        return "primary" if st.session_state['ts_period'] == period else "secondary"

    with col1:
        st.button("1 Ano", width='stretch', type=get_btn_type("1 Ano"), on_click=set_period, args=("1 Ano",))

    with col2:
        st.button("3 Anos", width='stretch', type=get_btn_type("3 Anos"), on_click=set_period, args=("3 Anos",))

    with col3:
        st.button("5 Anos", width='stretch', type=get_btn_type("5 Anos"), on_click=set_period, args=("5 Anos",))

    with col4:
        st.button("10 Anos", width='stretch', type=get_btn_type("10 Anos"), on_click=set_period, args=("10 Anos",))

    with col5:
        st.button("Tudo", width='stretch', type=get_btn_type("Tudo"), on_click=set_period, args=("Tudo",))

    st.divider()

    # Análise de tendência
    st.header("📊 Análise de Tendência")

    if aggregation == 'Empresas individuais' and len(selected_companies) > 0:
        # Calcular CAGR e volatilidade para cada empresa
        results = []

        for company in selected_companies:
            df_company = filter_by_tickers(df_filtered, [company])
            df_company = df_company.sort_values('Data_Trimestre')

            if len(df_company) >= 2:
                # CAGR
                start_value = df_company[metric].iloc[0]
                end_value = df_company[metric].iloc[-1]

                start_date = df_company['Data_Trimestre'].iloc[0]
                end_date = df_company['Data_Trimestre'].iloc[-1]
                years = (end_date - start_date).days / 365.25

                if years > 0:
                    cagr = calculate_cagr(start_value, end_value, years)
                else:
                    cagr = None

                # Volatilidade
                volatility = calculate_volatility(df_company[metric])

                results.append({
                    'Ticker': company,
                    'CAGR': cagr,
                    'Volatilidade': volatility,
                    'Períodos': len(df_company)
                })

        if results:
            df_trends = pd.DataFrame(results)

            # Formatar
            from src.utils.formatters import format_percent

            df_display = df_trends.copy()
            df_display['CAGR'] = df_display['CAGR'].apply(
                lambda x: format_percent(x) if pd.notna(x) else "N/A"
            )
            df_display['Volatilidade'] = df_display['Volatilidade'].apply(
                lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A"
            )

            st.dataframe(df_display, width='stretch', hide_index=True)

    st.divider()

    # Download
    st.header("💾 Download de Dados")

    render_export_buttons(df_plot)

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(traceback.format_exc())
