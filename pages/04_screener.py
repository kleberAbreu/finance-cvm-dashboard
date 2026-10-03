"""
Página 4: Screener - Filtro e Ranqueamento de Empresas.
"""
import streamlit as st
import pandas as pd
from src.data.loader import load_and_prepare_base
from src.data.preprocessor import get_latest_quarter_data, filter_by_metric_range
from src.components.sidebar import render_sidebar_filters, render_export_buttons
from config.settings import PARQUET_BASE_FILE

st.set_page_config(page_title="Screener - Dashboard CVM", page_icon="🔍", layout="wide")

st.title("🔍 Screener de Empresas")

# Aplicar filtros gerais
filters = render_sidebar_filters()

try:
    # Carregar dados
    df_base = load_and_prepare_base(PARQUET_BASE_FILE)
    df_latest = get_latest_quarter_data(df_base)

    # Layout: Filtros à esquerda, resultados à direita
    col_filter, col_results = st.columns([1, 2])

    with col_filter:
        st.header("⚙️ Critérios de Filtro")

        with st.form("screener_form"):
            st.subheader("Market Cap")
            market_cap_min = st.number_input(
                "Mínimo (bilhões R$)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key='screen_mc_min'
            )
            market_cap_max = st.number_input(
                "Máximo (bilhões R$)",
                min_value=0.0,
                value=1000.0,
                step=10.0,
                key='screen_mc_max'
            )

            st.divider()

            st.subheader("P/E")
            pe_min = st.number_input(
                "Mínimo",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key='screen_pe_min'
            )
            pe_max = st.number_input(
                "Máximo",
                min_value=0.0,
                value=100.0,
                step=5.0,
                key='screen_pe_max'
            )

            st.divider()

            st.subheader("EV/EBITDA")
            ev_min = st.number_input(
                "Mínimo",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key='screen_ev_min'
            )
            ev_max = st.number_input(
                "Máximo",
                min_value=0.0,
                value=50.0,
                step=2.0,
                key='screen_ev_max'
            )

            st.divider()

            st.subheader("P/B")
            pb_min = st.number_input(
                "Mínimo",
                min_value=0.0,
                value=0.0,
                step=0.5,
                key='screen_pb_min'
            )
            pb_max = st.number_input(
                "Máximo",
                min_value=0.0,
                value=20.0,
                step=1.0,
                key='screen_pb_max'
            )

            st.divider()

            st.subheader("DL/EV")
            dl_min = st.number_input(
                "Mínimo",
                min_value=-2.0,
                value=-2.0,
                step=0.1,
                key='screen_dl_min'
            )
            dl_max = st.number_input(
                "Máximo",
                min_value=-2.0,
                value=2.0,
                step=0.1,
                key='screen_dl_max'
            )

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                apply_button = st.form_submit_button("✅ Aplicar", width='stretch')
            with col2:
                reset_button = st.form_submit_button("🔄 Resetar", width='stretch')

    with col_results:
        st.header("📋 Resultados")

        # Aplicar filtros se botão pressionado
        if apply_button or 'screener_df' not in st.session_state:
            df_filtered = df_latest.copy()

            # Aplicar filtros de métricas
            df_filtered = filter_by_metric_range(
                df_filtered, 'Market Cap',
                market_cap_min * 1e9, market_cap_max * 1e9
            )

            df_filtered = filter_by_metric_range(
                df_filtered, 'P/E',
                pe_min, pe_max
            )

            df_filtered = filter_by_metric_range(
                df_filtered, 'EV/EBITDA',
                ev_min, ev_max
            )

            df_filtered = filter_by_metric_range(
                df_filtered, 'P/B',
                pb_min, pb_max
            )

            df_filtered = filter_by_metric_range(
                df_filtered, 'DL/EV',
                dl_min, dl_max
            )

            # Remover inf/nan
            from src.data.preprocessor import clean_dataframe
            df_filtered = clean_dataframe(df_filtered, remove_inf=True, remove_na=False)

            st.session_state.screener_df = df_filtered

        elif reset_button:
            st.session_state.screener_df = df_latest.copy()

        df_results = st.session_state.get('screener_df', df_latest)

        # Estatísticas rápidas
        total_results = len(df_results)
        total_available = len(df_latest)

        st.markdown(f"**Mostrando {total_results:,} de {total_available:,} empresas**")

        if total_results > 0:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_pe = df_results['P/E'].median()
                st.metric("P/E Mediano", f"{avg_pe:.2f}x" if pd.notna(avg_pe) else "N/A")

            with col2:
                avg_ev = df_results['EV/EBITDA'].median()
                st.metric("EV/EBITDA Mediano", f"{avg_ev:.2f}x" if pd.notna(avg_ev) else "N/A")

            with col3:
                avg_pb = df_results['P/B'].median()
                st.metric("P/B Mediano", f"{avg_pb:.2f}x" if pd.notna(avg_pb) else "N/A")

            with col4:
                total_mc = df_results['Market Cap'].sum()
                from src.utils.formatters import format_currency
                st.metric("Market Cap Total", format_currency(total_mc))

            st.divider()

            # Ordenação
            sort_col = st.selectbox(
                "Ordenar por:",
                options=['Market Cap', 'P/E', 'EV/EBITDA', 'P/B', 'EBITDA', 'Ticker'],
                index=0,
                key='sort_col'
            )

            sort_ascending = st.checkbox("Ordem crescente", value=False, key='sort_asc')

            df_sorted = df_results.sort_values(sort_col, ascending=sort_ascending)

            # Paginação
            rows_per_page = 50
            total_pages = (len(df_sorted) - 1) // rows_per_page + 1

            if total_pages > 1:
                page = st.selectbox(
                    f"Página (1-{total_pages}):",
                    options=range(1, total_pages + 1),
                    key='page_num'
                )
            else:
                page = 1

            start_idx = (page - 1) * rows_per_page
            end_idx = min(start_idx + rows_per_page, len(df_sorted))

            df_page = df_sorted.iloc[start_idx:end_idx]

            # Tabela de resultados
            cols_display = [
                'Ticker', 'Empresa', 'Tipo', 'Market Cap',
                'P/E', 'EV/EBITDA', 'P/B', 'DL/EV', 'EBITDA'
            ]

            df_display = df_page[cols_display].copy()

            # Formatar
            from src.utils.formatters import format_currency, format_multiple

            df_display['Market Cap'] = df_display['Market Cap'].apply(format_currency)
            df_display['EBITDA'] = df_display['EBITDA'].apply(format_currency)
            df_display['P/E'] = df_display['P/E'].apply(format_multiple)
            df_display['EV/EBITDA'] = df_display['EV/EBITDA'].apply(format_multiple)
            df_display['P/B'] = df_display['P/B'].apply(format_multiple)
            df_display['DL/EV'] = df_display['DL/EV'].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")

            st.dataframe(
                df_display,
                width='stretch',
                hide_index=True,
                height=600
            )

            # Download
            st.divider()

            render_export_buttons(df_sorted)

        else:
            st.warning("Nenhuma empresa encontrada com os critérios especificados")

    st.divider()

    # Presets salvos
    st.header("💾 Telas Predefinidas")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📉 Value Stocks (P/E < 15, P/B < 2)", width='stretch'):
            st.info("Feature será implementada: Aplicar filtros para Value Stocks")

    with col2:
        if st.button("📈 High Growth (EV/EBITDA < 10)", width='stretch'):
            st.info("Feature será implementada: Aplicar filtros para High Growth")

    with col3:
        if st.button("💰 Large Cap (MC > 10bi)", width='stretch'):
            st.info("Feature será implementada: Aplicar filtros para Large Cap")

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(traceback.format_exc())
