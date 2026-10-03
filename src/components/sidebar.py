"""
Filtros universais aplicados via sidebar.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Optional
from src.data.loader import (
    get_available_tickers, get_available_sectors, get_data_source_info,
    load_and_prepare_base
)
from config.settings import PARQUET_BASE_FILE
from src.publication import is_public_demo


def initialize_session_state():
    """Inicializa variáveis de estado da sessão."""
    if 'excel_file' not in st.session_state:
        st.session_state.excel_file = PARQUET_BASE_FILE

    if 'filtered_tickers' not in st.session_state:
        st.session_state.filtered_tickers = []

    if 'filtered_sectors' not in st.session_state:
        st.session_state.filtered_sectors = []

    if 'date_range' not in st.session_state:
        st.session_state.date_range = None

    if 'metric_filters' not in st.session_state:
        st.session_state.metric_filters = {}

    if 'only_valid_data' not in st.session_state:
        st.session_state.only_valid_data = True


def render_sidebar_filters():
    """
    Renderiza filtros na sidebar e retorna configuração de filtros.

    Returns:
        Dicionário com filtros aplicados
    """
    initialize_session_state()

    st.sidebar.title("🎯 Filtros")

    # --- FONTE DE DADOS ---
    st.sidebar.header("📂 Fonte de Dados")

    # Informações sobre pipeline
    from src.data.incremental_pipeline import get_incremental_info

    source_info = get_data_source_info()
    st.session_state.excel_file = source_info['paths']['base']
    info = get_incremental_info(source_info['paths']['base'])

    if source_info['using_sample']:
        st.sidebar.info(f"""
        ℹ️ **Amostra pública carregada**

        O dashboard está usando dados demonstrativos em `data/sample`.
        """)
    elif info['exists']:
        st.sidebar.success(f"""
        ✅ **Dados do pipeline carregados**

        Último trimestre: {info['last_quarter']}
        """)

        if info['can_increment']:
            st.sidebar.info(f"""
            📊 **{info['quarters_behind']} novo(s) trimestre(s) disponível(eis)**
            """)
    else:
        st.sidebar.warning("⚠️ Nenhum arquivo Parquet encontrado")

    st.sidebar.markdown("---")

    if not is_public_demo():
        st.sidebar.markdown("### ⚙️ Atualizar dados\nUse a página de execução do pipeline no ambiente local.")
        st.sidebar.divider()

    # --- FILTROS DE TEMPO ---
    st.sidebar.header("📅 Período")

    # Carregar dados para obter range de datas
    try:
        df_base = load_and_prepare_base(st.session_state.excel_file)

        # Variável para armazenar o date_range selecionado
        selected_date_range = None

        if 'Data_Trimestre' in df_base.columns:
            min_date = df_base['Data_Trimestre'].min()
            max_date = df_base['Data_Trimestre'].max()

            # Converter para date objects
            min_date = min_date.date() if hasattr(min_date, 'date') else min_date
            max_date = max_date.date() if hasattr(max_date, 'date') else max_date

            date_range = st.sidebar.date_input(
                "Intervalo de datas:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key='date_range_input'
            )

            # Armazenar o date_range
            if isinstance(date_range, tuple) and len(date_range) == 2:
                selected_date_range = date_range
                st.session_state.date_range = date_range
            elif hasattr(date_range, '__len__') and len(date_range) == 2:
                # Caso seja uma lista ou outro iterável
                selected_date_range = tuple(date_range)
                st.session_state.date_range = selected_date_range

        only_latest = st.sidebar.checkbox(
            "Apenas trimestre mais recente",
            value=False,
            key='only_latest'
        )

    except Exception as e:
        st.sidebar.error(f"Erro ao carregar dados: {str(e)}")
        return {}

    st.sidebar.divider()

    # Mostrar filtros ativos de data
    if only_latest:
        st.sidebar.info("📍 **Filtro ativo:** Apenas último trimestre")
    elif selected_date_range:
        st.sidebar.success(f"📅 **Período selecionado:** {selected_date_range[0]} a {selected_date_range[1]}")

    st.sidebar.divider()

    # --- FILTROS DE EMPRESA/SETOR ---
    st.sidebar.header("🏢 Empresas & Setores")

    # Carregar listas
    all_tickers = get_available_tickers(st.session_state.excel_file)
    all_sectors = get_available_sectors(st.session_state.excel_file)

    # Filtro de setores (aplicar primeiro)
    selected_sectors = st.sidebar.multiselect(
        f"Setores ({len(all_sectors)} disponíveis):",
        options=all_sectors,
        default=[],
        key='sector_filter'
    )

    # Filtrar tickers por setor se necessário
    available_tickers = all_tickers
    if selected_sectors:
        df_filtered = df_base[df_base['Tipo'].isin(selected_sectors)]
        available_tickers = sorted(df_filtered['Ticker'].dropna().astype(str).unique().tolist())

    # Filtro de tickers
    selected_tickers = st.sidebar.multiselect(
        f"Empresas ({len(available_tickers)} disponíveis):",
        options=available_tickers,
        default=[],
        key='ticker_filter'
    )

    # Quick filter: Top N por Market Cap
    top_n = st.sidebar.slider(
        "Filtro rápido: Top N por Market Cap",
        min_value=0,
        max_value=50,
        value=0,
        step=5,
        key='top_n_filter',
        help="0 = desabilitado"
    )

    # Mostrar se Top N está ativo
    if top_n > 0:
        st.sidebar.success(f"🔝 **Top {top_n} empresas** por Market Cap")

    st.sidebar.divider()

    # --- FILTROS DE MÉTRICAS ---
    st.sidebar.header("📊 Métricas")

    with st.sidebar.expander("Market Cap", expanded=False):
        market_cap_enabled = st.checkbox("Aplicar filtro", key="market_cap_enabled", value=False)
        market_cap_range = st.slider(
            "Range (em bilhões)",
            min_value=0.0,
            max_value=500.0,
            value=(0.0, 500.0),
            step=10.0,
            key='market_cap_filter'
        )

    with st.sidebar.expander("P/E", expanded=False):
        pe_enabled = st.checkbox("Aplicar filtro", key="pe_enabled", value=False)
        pe_range = st.slider(
            "Range",
            min_value=0.0,
            max_value=100.0,
            value=(0.0, 100.0),
            step=5.0,
            key='pe_filter'
        )

    with st.sidebar.expander("EV/EBITDA", expanded=False):
        ev_ebitda_enabled = st.checkbox("Aplicar filtro", key="ev_ebitda_enabled", value=False)
        ev_ebitda_range = st.slider(
            "Range",
            min_value=0.0,
            max_value=50.0,
            value=(0.0, 50.0),
            step=2.0,
            key='ev_ebitda_filter'
        )

    with st.sidebar.expander("P/B", expanded=False):
        pb_enabled = st.checkbox("Aplicar filtro", key="pb_enabled", value=False)
        pb_range = st.slider(
            "Range",
            min_value=0.0,
            max_value=20.0,
            value=(0.0, 20.0),
            step=1.0,
            key='pb_filter'
        )

    only_valid = st.sidebar.checkbox(
        "Tratar valores infinitos como ausentes",
        value=True,
        key='only_valid_data_cb'
    )

    st.session_state.only_valid_data = only_valid

    # Limpar cache
    if not is_public_demo() and st.sidebar.button("🔄 Limpar Cache", key='clear_cache'):
        from src.data.loader import clear_cache
        clear_cache()
        st.sidebar.success("Cache limpo!")
        st.rerun()

    # --- RETORNAR CONFIGURAÇÃO DE FILTROS ---
    # Pegar date_range do session_state ou usar selected_date_range
    final_date_range = None
    if not only_latest:
        if 'date_range' in st.session_state and st.session_state.date_range:
            final_date_range = st.session_state.date_range
        elif 'selected_date_range' in locals() and selected_date_range:
            final_date_range = selected_date_range

    filters = {
        'date_range': final_date_range,
        'only_latest': only_latest,
        'tickers': selected_tickers,
        'sectors': selected_sectors,
        'top_n': top_n if top_n > 0 else None,
        'market_cap': (market_cap_range[0] * 1e9, market_cap_range[1] * 1e9) if market_cap_enabled else None,
        'pe': pe_range if pe_enabled else None,
        'ev_ebitda': ev_ebitda_range if ev_ebitda_enabled else None,
        'pb': pb_range if pb_enabled else None,
        'only_valid': only_valid
    }

    return filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Aplica todos os filtros a um DataFrame.

    Args:
        df: DataFrame original
        filters: Dicionário de filtros retornado por render_sidebar_filters()

    Returns:
        DataFrame filtrado
    """
    from src.data.preprocessor import (
        filter_by_date_range, filter_by_tickers, filter_by_sectors,
        filter_by_metric_range, get_top_n_by_metric, get_latest_quarter_data,
        clean_dataframe
    )

    df_filtered = df.copy()

    # ===== ORDEM CORRETA DE FILTROS =====

    # 1. PRIMEIRO: Top N (se ativo, pega top N empresas baseado no último trimestre)
    #    Isso identifica quais empresas mostrar ANTES de filtrar por data
    selected_tickers_from_top_n = None
    if filters.get('top_n'):
        # Pegar top N empresas baseado no último trimestre disponível
        df_top_n = get_top_n_by_metric(
            df_filtered, 'Market Cap',
            n=filters['top_n'],
            group_col='Ticker'
        )
        # Guardar os tickers do Top N
        if 'Ticker' in df_top_n.columns:
            selected_tickers_from_top_n = df_top_n['Ticker'].unique().tolist()
            # Filtrar dataframe completo para incluir TODA A HISTÓRIA dessas empresas
            df_filtered = df_filtered[df_filtered['Ticker'].isin(selected_tickers_from_top_n)]

    # 2. Filtro de setores (aplicar antes de tickers)
    if filters.get('sectors'):
        df_filtered = filter_by_sectors(df_filtered, filters['sectors'])

    # 3. Filtro de tickers (se não foi usado Top N)
    if filters.get('tickers'):
        df_filtered = filter_by_tickers(df_filtered, filters['tickers'])

    # 4. Filtro de data (DEPOIS de selecionar empresas, mostra histórico delas)
    if filters.get('only_latest'):
        df_filtered = get_latest_quarter_data(df_filtered)
    elif filters.get('date_range'):
        date_range = filters['date_range']
        if isinstance(date_range, tuple) and len(date_range) == 2:
            df_filtered = filter_by_date_range(df_filtered, date_range[0], date_range[1])

    # 5. Filtros de métricas (valores específicos)
    if filters.get('market_cap'):
        df_filtered = filter_by_metric_range(
            df_filtered, 'Market Cap',
            filters['market_cap'][0], filters['market_cap'][1]
        )

    if filters.get('pe'):
        df_filtered = filter_by_metric_range(
            df_filtered, 'P/E',
            filters['pe'][0], filters['pe'][1]
        )

    if filters.get('ev_ebitda'):
        df_filtered = filter_by_metric_range(
            df_filtered, 'EV/EBITDA',
            filters['ev_ebitda'][0], filters['ev_ebitda'][1]
        )

    if filters.get('pb'):
        df_filtered = filter_by_metric_range(
            df_filtered, 'P/B',
            filters['pb'][0], filters['pb'][1]
        )

    # 6. Limpar dados inválidos
    if filters.get('only_valid'):
        df_filtered = clean_dataframe(df_filtered, remove_inf=True, remove_na=False)

    return df_filtered


def prepare_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """Carry the demonstration provenance into every exported row."""
    result = df.copy()
    if is_public_demo():
        result['Fonte'] = 'Amostra demonstrativa congelada; não são cotações atuais'
        result['Unidade_monetaria'] = 'BRL (reais); não milhões'
    return result


def render_export_buttons(df: pd.DataFrame):
    """
    Renderiza botões de exportação para CSV e Excel na sidebar.
    Deve ser chamado APÓS a aplicação dos filtros para exportar os dados corretos.
    """
    if len(df) == 0:
        return
        
    st.sidebar.divider()
    st.sidebar.header("💾 Exportação")
    
    col1, col2 = st.sidebar.columns(2)
    
    # Gerar CSV
    export_df = prepare_export_data(df)
    csv = export_df.to_csv(index=False).encode('utf-8')
    col1.download_button(
        label="📥 CSV",
        data=csv,
        file_name="dados_cvm_export.csv",
        mime="text/csv",
        key='download_csv',
        width='stretch'
    )
    
    # Gerar Excel em memória
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Dados')
    
    col2.download_button(
        label="📊 Excel",
        data=buffer.getvalue(),
        file_name="dados_cvm_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key='download_excel',
        width='stretch'
    )
