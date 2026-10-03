"""
Página 2: Company Analysis - Análise Individual de Empresas.
"""
import streamlit as st
from src.components.theme import page_intro, plot_chart
import pandas as pd
from src.data.loader import load_and_prepare_base, get_available_tickers
from src.data.preprocessor import filter_by_tickers
from src.components.sidebar import render_sidebar_filters, apply_filters, render_export_buttons
from src.components.metrics_cards import render_company_profile_card
from src.components.charts import create_time_series_chart, create_distribution_plot
from config.settings import PARQUET_BASE_FILE

st.set_page_config(page_title="Company Analysis - Dashboard CVM", page_icon="🏢", layout="wide")

page_intro('Análise de empresas', 'Explore os fundamentos de cada empresa e compare sua trajetória financeira.')

# Aplicar filtros
filters = render_sidebar_filters()

try:
    # Carregar dados e aplicar filtros
    df_base = load_and_prepare_base(PARQUET_BASE_FILE)
    df_filtered = apply_filters(df_base, filters)

    # Extrair tickers disponíveis do dataframe filtrado
    all_tickers = sorted(df_filtered['Ticker'].dropna().astype(str).unique().tolist())

    if len(df_filtered) == 0:
        st.warning("Nenhum dado disponível com os filtros aplicados")
        st.stop()

    # Seleção de empresa principal
    st.header("Selecione a Empresa")

    selected_ticker = st.selectbox(
        "Buscar empresa por ticker:",
        options=all_tickers,
        index=0 if len(all_tickers) > 0 else None,
        key='main_ticker'
    )

    if not selected_ticker:
        st.warning("Selecione uma empresa para análise")
        st.stop()

    # Dados da empresa selecionada (usar df_filtered em vez de df_base)
    df_company = filter_by_tickers(df_filtered, [selected_ticker])

    if len(df_company) == 0:
        st.error(f"Nenhum dado encontrado para {selected_ticker}")
        st.stop()

    # Card de perfil
    render_company_profile_card(selected_ticker, df_company)

    st.divider()

    # Abas de demonstrativos
    st.header("Demonstrativos Financeiros")

    tab1, tab2, tab3 = st.tabs(["Balanço Patrimonial", "Demonstração de Resultados", "Múltiplos de Valuation"])

    with tab1:
        st.subheader("Evolução do Balanço")

        col1, col2 = st.columns([3, 1])

        with col1:
            metrics_balanco = ['Ativo Total', 'Caixa', 'Dívida Líquida', 'Patrimônio Líquido']
            selected_metrics = st.multiselect(
                "Selecione métricas:",
                options=metrics_balanco,
                default=metrics_balanco[:2],
                key='balanco_metrics'
            )

        with col2:
            compare_benchmarks_1 = st.checkbox(
                "📊 vs Setor & Mercado",
                value=False,
                key='compare_balanco',
                help="Adiciona medianas do setor e mercado"
            )

        if selected_metrics:
            company_sector = df_company.iloc[0]['Tipo']

            fig = create_time_series_chart(
                df_company,
                metric=selected_metrics[0],
                companies=[selected_ticker],
                title=f"Evolução de {', '.join(selected_metrics)}"
            )

            # Adicionar outras métricas da empresa
            for metric in selected_metrics[1:]:
                df_metric = df_company[['Data_Trimestre', metric]].dropna()
                fig.add_scatter(
                    x=df_metric['Data_Trimestre'],
                    y=df_metric[metric],
                    name=metric,
                    mode='lines+markers'
                )

            # Adicionar benchmarks
            if compare_benchmarks_1 and len(selected_metrics) == 1:
                metric = selected_metrics[0]

                # Mediana do setor
                df_sector = df_filtered[df_filtered['Tipo'] == company_sector]
                df_sector_agg = df_sector.groupby('Data_Trimestre')[metric].median().reset_index()
                fig.add_scatter(
                    x=df_sector_agg['Data_Trimestre'],
                    y=df_sector_agg[metric],
                    name=f'Setor: {company_sector}',
                    mode='lines',
                    line=dict(dash='dash', width=2.5, color='#B58C50'),
                    opacity=0.8
                )

                # Mediana do mercado
                df_market_agg = df_filtered.groupby('Data_Trimestre')[metric].median().reset_index()
                fig.add_scatter(
                    x=df_market_agg['Data_Trimestre'],
                    y=df_market_agg[metric],
                    name='Mercado',
                    mode='lines',
                    line=dict(dash='dot', width=2.5, color='gray'),
                    opacity=0.8
                )

            plot_chart(fig, width='stretch')

            if compare_benchmarks_1 and len(selected_metrics) > 1:
                st.info("💡 Comparação disponível apenas para 1 métrica por vez")

    with tab2:
        st.subheader("Evolução de Resultados")

        col1, col2 = st.columns([3, 1])

        with col1:
            metrics_resultado = ['Lucro Líquido', 'EBITDA', 'Resultado Financeiro']
            selected_metrics = st.multiselect(
                "Selecione métricas:",
                options=metrics_resultado,
                default=['Lucro Líquido', 'EBITDA'],
                key='resultado_metrics'
            )

        with col2:
            compare_benchmarks_2 = st.checkbox(
                "📊 vs Setor & Mercado",
                value=False,
                key='compare_resultado',
                help="Adiciona medianas do setor e mercado"
            )

        if selected_metrics:
            company_sector = df_company.iloc[0]['Tipo']

            fig = create_time_series_chart(
                df_company,
                metric=selected_metrics[0],
                companies=[selected_ticker],
                title=f"Evolução de {', '.join(selected_metrics)}"
            )

            for metric in selected_metrics[1:]:
                df_metric = df_company[['Data_Trimestre', metric]].dropna()
                fig.add_scatter(
                    x=df_metric['Data_Trimestre'],
                    y=df_metric[metric],
                    name=metric,
                    mode='lines+markers'
                )

            # Adicionar benchmarks
            if compare_benchmarks_2 and len(selected_metrics) == 1:
                metric = selected_metrics[0]

                # Mediana do setor
                df_sector = df_filtered[df_filtered['Tipo'] == company_sector]
                df_sector_agg = df_sector.groupby('Data_Trimestre')[metric].median().reset_index()
                fig.add_scatter(
                    x=df_sector_agg['Data_Trimestre'],
                    y=df_sector_agg[metric],
                    name=f'Setor: {company_sector}',
                    mode='lines',
                    line=dict(dash='dash', width=2.5, color='#B58C50'),
                    opacity=0.8
                )

                # Mediana do mercado
                df_market_agg = df_filtered.groupby('Data_Trimestre')[metric].median().reset_index()
                fig.add_scatter(
                    x=df_market_agg['Data_Trimestre'],
                    y=df_market_agg[metric],
                    name='Mercado',
                    mode='lines',
                    line=dict(dash='dot', width=2.5, color='gray'),
                    opacity=0.8
                )

            plot_chart(fig, width='stretch')

            if compare_benchmarks_2 and len(selected_metrics) > 1:
                st.info("💡 Comparação disponível apenas para 1 métrica por vez")

    with tab3:
        st.subheader("Evolução de Múltiplos")

        col1, col2 = st.columns([3, 1])

        with col1:
            metrics_multiplos = ['P/E', 'EV/EBITDA', 'P/B', 'DL/EV']
            selected_metrics = st.multiselect(
                "Selecione múltiplos:",
                options=metrics_multiplos,
                default=['P/E', 'EV/EBITDA'],
                key='multiplos_metrics'
            )

        with col2:
            compare_benchmarks_3 = st.checkbox(
                "📊 vs Setor & Mercado",
                value=False,
                key='compare_multiplos',
                help="Adiciona medianas do setor e mercado"
            )

        if selected_metrics:
            company_sector = df_company.iloc[0]['Tipo']

            fig = create_time_series_chart(
                df_company,
                metric=selected_metrics[0],
                companies=[selected_ticker],
                title=f"Evolução de {', '.join(selected_metrics)}"
            )

            for metric in selected_metrics[1:]:
                df_metric = df_company[['Data_Trimestre', metric]].dropna()
                fig.add_scatter(
                    x=df_metric['Data_Trimestre'],
                    y=df_metric[metric],
                    name=metric,
                    mode='lines+markers'
                )

            # Adicionar benchmarks
            if compare_benchmarks_3 and len(selected_metrics) == 1:
                metric = selected_metrics[0]

                # Mediana do setor
                df_sector = df_filtered[df_filtered['Tipo'] == company_sector]
                df_sector_agg = df_sector.groupby('Data_Trimestre')[metric].median().reset_index()
                fig.add_scatter(
                    x=df_sector_agg['Data_Trimestre'],
                    y=df_sector_agg[metric],
                    name=f'Setor: {company_sector}',
                    mode='lines',
                    line=dict(dash='dash', width=2.5, color='#B58C50'),
                    opacity=0.8
                )

                # Mediana do mercado
                df_market_agg = df_filtered.groupby('Data_Trimestre')[metric].median().reset_index()
                fig.add_scatter(
                    x=df_market_agg['Data_Trimestre'],
                    y=df_market_agg[metric],
                    name='Mercado',
                    mode='lines',
                    line=dict(dash='dot', width=2.5, color='gray'),
                    opacity=0.8
                )

            plot_chart(fig, width='stretch')

            if compare_benchmarks_3 and len(selected_metrics) > 1:
                st.info("💡 Comparação disponível apenas para 1 métrica por vez")

    st.divider()

    # Comparação com peers
    st.header("Comparação com Peers")

    # Pegar setor da empresa
    company_sector = df_company.iloc[0]['Tipo']

    st.write(f"**Setor:** {company_sector}")

    # Listar empresas do mesmo setor (usar df_filtered)
    df_sector = df_filtered[df_filtered['Tipo'] == company_sector]
    sector_tickers = sorted(df_sector['Ticker'].dropna().astype(str).unique().tolist())

    # Remover empresa principal da lista
    if selected_ticker in sector_tickers:
        sector_tickers.remove(selected_ticker)

    peers = st.multiselect(
        f"Selecione até 4 empresas do setor {company_sector} para comparar:",
        options=sector_tickers,
        default=sector_tickers[:4] if len(sector_tickers) >= 4 else sector_tickers,
        max_selections=4,
        key='peers'
    )

    if peers:
        # Adicionar empresa principal
        all_companies = [selected_ticker] + peers

        # Métrica para comparação
        comparison_metric = st.selectbox(
            "Métrica para comparação:",
            options=['Market Cap', 'EBITDA', 'P/E', 'EV/EBITDA', 'P/B'],
            key='comparison_metric'
        )

        # Gráfico de comparação (usar df_filtered)
        df_comparison = filter_by_tickers(df_filtered, all_companies)

        fig = create_time_series_chart(
            df_comparison,
            metric=comparison_metric,
            companies=all_companies,
            title=f"Comparação: {comparison_metric}"
        )

        plot_chart(fig, width='stretch')

        # Tabela lado a lado (dados mais recentes)
        st.subheader("Comparação de Métricas (Trimestre Mais Recente)")

        df_latest = df_comparison.sort_values('Data_Trimestre').groupby('Ticker').tail(1)

        cols_display = ['Ticker', 'Empresa', 'Market Cap', 'P/E', 'EV/EBITDA', 'P/B', 'EBITDA']
        df_table = df_latest[cols_display].copy()

        # Formatar
        from src.utils.formatters import format_currency, format_multiple
        df_table['Market Cap'] = df_table['Market Cap'].apply(format_currency)
        df_table['EBITDA'] = df_table['EBITDA'].apply(format_currency)
        df_table['P/E'] = df_table['P/E'].apply(format_multiple)
        df_table['EV/EBITDA'] = df_table['EV/EBITDA'].apply(format_multiple)
        df_table['P/B'] = df_table['P/B'].apply(format_multiple)

        st.dataframe(df_table, width='stretch', hide_index=True)

    st.divider()

    # Benchmarking vs Setor
    st.header("Benchmarking vs Setor")

    # Estatísticas do setor
    df_sector_latest = df_sector.sort_values('Data_Trimestre').groupby('Ticker').tail(1)

    col1, col2, col3, col4 = st.columns(4)

    # Pegar valores da empresa
    company_latest = df_company.sort_values('Data_Trimestre').iloc[-1]

    with col1:
        sector_median_pe = df_sector_latest['P/E'].median()
        company_pe = company_latest['P/E']

        st.metric(
            "P/E",
            f"{company_pe:.2f}x" if pd.notna(company_pe) else "N/A",
            f"Setor: {sector_median_pe:.2f}x" if pd.notna(sector_median_pe) else "N/A"
        )

    with col2:
        sector_median_ev = df_sector_latest['EV/EBITDA'].median()
        company_ev = company_latest['EV/EBITDA']

        st.metric(
            "EV/EBITDA",
            f"{company_ev:.2f}x" if pd.notna(company_ev) else "N/A",
            f"Setor: {sector_median_ev:.2f}x" if pd.notna(sector_median_ev) else "N/A"
        )

    with col3:
        sector_median_pb = df_sector_latest['P/B'].median()
        company_pb = company_latest['P/B']

        st.metric(
            "P/B",
            f"{company_pb:.2f}x" if pd.notna(company_pb) else "N/A",
            f"Setor: {sector_median_pb:.2f}x" if pd.notna(sector_median_pb) else "N/A"
        )

    with col4:
        from src.utils.calculations import calculate_percentile_rank

        if pd.notna(company_pe):
            percentile = calculate_percentile_rank(df_sector_latest['P/E'], company_pe)
            st.metric(
                "Percentil P/E",
                f"{percentile:.0f}º"
            )
        else:
            st.metric("Percentil P/E", "N/A")

    # Renderizar botões de exportação
    render_export_buttons(df_filtered)

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(traceback.format_exc())
