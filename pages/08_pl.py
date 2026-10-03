"""
Página 8: P&L + Balanço Patrimonial em formato de tabela.

Permite filtrar por múltiplas empresas ou setores e visualizar
o DRE e o Balanço Patrimonial por período (trimestre) em colunas.
"""
import streamlit as st
import pandas as pd
from src.components.sidebar import prepare_export_data
import numpy as np
from src.data.loader import load_and_prepare_base, get_available_tickers, get_available_sectors
from src.data.preprocessor import filter_by_tickers, filter_by_sectors
from src.components.sidebar import render_sidebar_filters, apply_filters, render_export_buttons
from src.utils.formatters import format_currency
from config.settings import PARQUET_BASE_FILE

st.set_page_config(page_title="P&L - Dashboard CVM", page_icon="📋", layout="wide")


# ========================== CONFIGURAÇÃO DAS CONTAS ==========================

# Contas DRE — ordem do topo (receita) ao bottom (lucro)
# (display_name, column_name, is_subtotal)
DRE_ACCOUNTS = [
    ('Receita Líquida',        'Receita Líquida',        False),
    ('(-) CPV / CMV',          'CPV',                    False),
    ('= Lucro Bruto',          'Lucro Bruto',            True),
    ('(-) Despesas Oper.',     'Despesas Operacionais',  False),
    ('= EBIT',                 'EBIT',                   True),
    ('(+) D&A',                'D&A',                    False),
    ('= EBITDA',               'EBITDA',                 True),
    ('(+/-) Res. Financeiro',  'Resultado Financeiro',   False),
    ('(-) IR / CSLL',          'IR',                     False),
    ('= Lucro Líquido',        'Lucro Líquido',          True),
]

# Indicadores derivados
# (display_name, indicator_key, format_type)
INDICATORS = [
    ('Margem Bruta (%)',    'margem_bruta',   'pct'),
    ('Margem EBITDA (%)',   'margem_ebitda',  'pct'),
    ('Margem Líquida (%)', 'margem_liquida', 'pct'),
    ('ROE (%)',             'roe',            'pct'),
    ('ROA (%)',             'roa',            'pct'),
    ('DL / EBITDA',         'dl_ebitda',      'x'),
]

SUBTOTAL_ROWS = ['= Lucro Bruto', '= EBIT', '= EBITDA', '= Lucro Líquido']
SEPARATOR_LABEL = '─' * 20
PCT_INDICATORS = ['Margem Bruta (%)', 'Margem EBITDA (%)', 'Margem Líquida (%)', 'ROE (%)', 'ROA (%)']

# ========================== CONFIGURAÇÃO DO BALANÇO ==========================

# Bloco ATIVO — (display_name, column_name, is_subtotal, indent)
ATIVO_ACCOUNTS = [
    ('Ativo Circulante',        'Ativo Circulante',        True,  0),
    ('  Caixa e Equiv.',        'Caixa',                   False, 1),
    ('  Aplicações Financeiras','Aplicações Financeiras',  False, 1),
    ('  Contas a Receber',      'Contas a Receber',        False, 1),
    ('  Estoques',              'Estoques',                False, 1),
    ('Ativo Não Circulante',    'Ativo Não Circulante',    True,  0),
    ('  Imobilizado',           'Imobilizado',             False, 1),
    ('  Intangível',            'Intangível',              False, 1),
    ('= Ativo Total',           'Ativo Total',             True,  0),
]

# Bloco PASSIVO — (display_name, column_name, is_subtotal, indent)
PASSIVO_ACCOUNTS = [
    ('Passivo Circulante',      'Passivo Circulante',      True,  0),
    ('Passivo Não Circulante',  'Passivo Não Circulante',  True,  0),
    ('  Dívida Bruta',          'Dívida Bruta',            False, 1),
    ('  Dívida Líquida',        'Dívida Líquida',          False, 1),
    ('Patrimônio Líquido',      'Patrimônio Líquido',      True,  0),
    ('= Passivo + PL',          'Passivo Total',           True,  0),
]

BP_SUBTOTAL_ROWS = {
    'Ativo Circulante', 'Ativo Não Circulante', '= Ativo Total',
    'Passivo Circulante', 'Passivo Não Circulante', 'Patrimônio Líquido', '= Passivo + PL',
}
BP_SEPARATOR = '═' * 20

# ========================== CONFIGURAÇÃO DO DFC ==========================

DFC_ACCOUNTS = [
    ('FCO — Caixa Operacional',      'FCO',                           True),
    ('  Caixa Gerado nas Operações', 'Caixa Gerado nas Operações',   False),
    ('  Variações Ativos/Passivos',  'Variações Ativos e Passivos',  False),
    ('  Outros (Operacional)',       'Outros (Operacional)',          False),
    ('FCI — Caixa Investimento',     'FCI',                           True),
    ('FCF — Caixa Financiamento',    'FCF',                           True),
    ('Variação Cambial',             'Variação Cambial',              False),
    ('= Variação Líquida de Caixa',  'Variação Líquida de Caixa',    True),
    ('  Saldo Inicial de Caixa',     'Saldo Inicial de Caixa',        False),
    ('  Saldo Final de Caixa',       'Saldo Final de Caixa',          False),
    ('(memo) D&A',                   'D&A',                           False),
]
DFC_SUBTOTAL_ROWS = {'FCO — Caixa Operacional', 'FCI — Caixa Investimento', 'FCF — Caixa Financiamento', '= Variação Líquida de Caixa'}


# ========================== FUNÇÕES AUXILIARES ==========================

def _calc_indicator(row: pd.Series, key: str):
    """Calcula um indicador derivado a partir de uma linha do DataFrame."""
    try:
        if key == 'margem_bruta':
            receita = row.get('Receita Líquida')
            lucro_bruto = row.get('Lucro Bruto')
            if pd.notna(receita) and receita != 0 and pd.notna(lucro_bruto):
                return lucro_bruto / receita
            return None

        elif key == 'margem_ebitda':
            receita = row.get('Receita Líquida')
            ebitda = row.get('EBITDA')
            if pd.notna(receita) and receita != 0 and pd.notna(ebitda):
                return ebitda / receita
            return None

        elif key == 'margem_liquida':
            receita = row.get('Receita Líquida')
            ll = row.get('Lucro Líquido')
            if pd.notna(receita) and receita != 0 and pd.notna(ll):
                return ll / receita
            return None

        elif key == 'roe':
            ll = row.get('Lucro Líquido')
            pl = row.get('Patrimônio Líquido')
            if pd.notna(pl) and pl != 0 and pd.notna(ll):
                return ll / pl
            return None

        elif key == 'roa':
            ll = row.get('Lucro Líquido')
            at = row.get('Ativo Total')
            if pd.notna(at) and at != 0 and pd.notna(ll):
                return ll / at
            return None

        elif key == 'dl_ebitda':
            dl = row.get('Dívida Líquida')
            ebitda = row.get('EBITDA')
            if pd.notna(ebitda) and ebitda != 0 and pd.notna(dl):
                return dl / ebitda
            return None

    except Exception:
        return None
    return None


def _to_scalar(val):
    """Extrai escalar de um valor que pode ser Series/array (índices duplicados)."""
    if isinstance(val, pd.Series):
        return val.iloc[0] if not val.empty else None
    if isinstance(val, np.ndarray):
        return val.flat[0] if val.size > 0 else None
    return val


def format_pl_value(val, row_name: str) -> str:
    """Formata valor para exibição na tabela P&L."""
    val = _to_scalar(val)

    if val is None:
        return "—"

    try:
        if pd.isna(val) or np.isinf(float(val)):
            return "—"
    except (TypeError, ValueError):
        return "—"

    # Separador visual
    if row_name.startswith('─'):
        return ""

    # Indicadores percentuais
    if row_name in PCT_INDICATORS:
        return f"{float(val) * 100:.1f}%".replace('.', ',')

    # Múltiplo (DL/EBITDA)
    if row_name == 'DL / EBITDA':
        return f"{float(val):.2f}x".replace('.', ',')

    # Valor monetário
    return format_currency(val)


def build_bp_table(df_company: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói a tabela de Balanço Patrimonial pivotada.
    Linhas = contas do Ativo (bloco 1) + separador + contas do Passivo (bloco 2)
    Colunas = trimestres ordenados
    """
    df_sorted = (
        df_company
        .sort_values('Data_Trimestre')
        .drop_duplicates(subset=['Data_Trimestre'], keep='last')
        .reset_index(drop=True)
    )

    if 'Trimestre' in df_sorted.columns:
        trimestres = df_sorted['Trimestre'].astype(str).tolist()
    else:
        trimestres = (
            df_sorted['Data_Trimestre'].dt.year.astype(str) + 'Q' +
            df_sorted['Data_Trimestre'].dt.quarter.astype(str)
        ).tolist()

    # Unicidade de labels
    seen: dict = {}
    unique_trimestres = []
    for t in trimestres:
        count = seen.get(t, 0)
        seen[t] = count + 1
        unique_trimestres.append(f"{t}.{count}" if count > 0 else t)
    trimestres = unique_trimestres

    available_cols = set(df_sorted.columns)
    rows: dict = {}

    # Bloco ATIVO
    for display_name, col_name, is_subtotal, indent in ATIVO_ACCOUNTS:
        if col_name in available_cols:
            rows[display_name] = df_sorted[col_name].tolist()

    # Separador entre blocos
    rows[BP_SEPARATOR] = [None] * len(trimestres)

    # Bloco PASSIVO + PL
    for display_name, col_name, is_subtotal, indent in PASSIVO_ACCOUNTS:
        if col_name in available_cols:
            rows[display_name] = df_sorted[col_name].tolist()

    if not rows or all(k == BP_SEPARATOR for k in rows):
        return pd.DataFrame()

    df_table = pd.DataFrame(rows, index=trimestres).T
    df_table.index.name = 'Conta'
    return df_table


def render_bp_table(df_table: pd.DataFrame, key_prefix: str):
    """Renderiza a tabela de Balanço Patrimonial com estilos."""
    if df_table.empty:
        st.info("⚠️ Dados de Balanço Patrimonial não disponíveis. Reprocesse o pipeline para incluir as novas contas.")
        return

    df_display = df_table.copy().astype(object)

    for row_name in df_display.index:
        for col in df_display.columns:
            val = _to_scalar(df_table.loc[row_name, col])
            if row_name == BP_SEPARATOR or (val is None):
                df_display.loc[row_name, col] = "—"
                continue
            try:
                if pd.isna(val) or np.isinf(float(val)):
                    df_display.loc[row_name, col] = "—"
                    continue
            except (TypeError, ValueError):
                df_display.loc[row_name, col] = "—"
                continue
            df_display.loc[row_name, col] = format_currency(val)

    def _highlight_bp(row):
        rn = row.name
        if rn in BP_SUBTOTAL_ROWS:
            return ['font-weight: bold; background-color: rgba(16, 185, 129, 0.10)'] * len(row)
        elif rn == BP_SEPARATOR:
            return ['border-top: 2px solid #555; font-size: 2px; color: transparent'] * len(row)
        return [''] * len(row)

    def _color_negatives_bp(val):
        if isinstance(val, str) and val.strip().startswith('-'):
            return 'color: #ef4444'
        return ''

    styled = df_display.style \
        .apply(_highlight_bp, axis=1) \
        .applymap(_color_negatives_bp)

    st.dataframe(
        styled,
        width='stretch',
        height=min(45 * len(df_display) + 40, 700)
    )

    csv = prepare_export_data(df_table).to_csv()
    st.download_button(
        label="📥 Exportar Balanço",
        data=csv,
        file_name=f"balanco_{key_prefix}.csv",
        mime="text/csv",
        key=f'download_bp_{key_prefix}'
    )


def build_dfc_table(df_company: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói a tabela de Fluxo de Caixa pivotada.
    Linhas = contas DFC (FCO, FCI, FCF, D&A)
    Colunas = trimestres ordenados
    """
    df_sorted = (
        df_company
        .sort_values('Data_Trimestre')
        .drop_duplicates(subset=['Data_Trimestre'], keep='last')
        .reset_index(drop=True)
    )

    if 'Trimestre' in df_sorted.columns:
        trimestres = df_sorted['Trimestre'].astype(str).tolist()
    else:
        trimestres = (
            df_sorted['Data_Trimestre'].dt.year.astype(str) + 'Q' +
            df_sorted['Data_Trimestre'].dt.quarter.astype(str)
        ).tolist()

    # Unicidade de labels
    seen: dict = {}
    unique_trimestres = []
    for t in trimestres:
        count = seen.get(t, 0)
        seen[t] = count + 1
        unique_trimestres.append(f"{t}.{count}" if count > 0 else t)
    trimestres = unique_trimestres

    available_cols = set(df_sorted.columns)
    rows: dict = {}

    for display_name, col_name, is_subtotal in DFC_ACCOUNTS:
        if col_name in available_cols:
            rows[display_name] = df_sorted[col_name].tolist()

    if not rows:
        return pd.DataFrame()

    df_table = pd.DataFrame(rows, index=trimestres).T
    df_table.index.name = 'Conta'
    return df_table


def render_dfc_table(df_table: pd.DataFrame, key_prefix: str):
    """Renderiza a tabela de Fluxo de Caixa com estilos."""
    if df_table.empty:
        st.info("⚠️ Dados de Fluxo de Caixa não disponíveis. Reprocesse o pipeline para incluir FCO, FCI e FCF.")
        return

    df_display = df_table.copy().astype(object)

    for row_name in df_display.index:
        for col in df_display.columns:
            val = _to_scalar(df_table.loc[row_name, col])
            if val is None:
                df_display.loc[row_name, col] = "—"
                continue
            try:
                if pd.isna(val) or np.isinf(float(val)):
                    df_display.loc[row_name, col] = "—"
                    continue
            except (TypeError, ValueError):
                df_display.loc[row_name, col] = "—"
                continue
            df_display.loc[row_name, col] = format_currency(val)

    def _highlight_dfc(row):
        rn = row.name
        if rn in DFC_SUBTOTAL_ROWS:
            return ['font-weight: bold; background-color: rgba(59, 130, 246, 0.10)'] * len(row)
        return [''] * len(row)

    def _color_negatives_dfc(val):
        if isinstance(val, str) and val.strip().startswith('-'):
            return 'color: #ef4444'
        return ''

    styled = df_display.style \
        .apply(_highlight_dfc, axis=1) \
        .applymap(_color_negatives_dfc)

    st.dataframe(
        styled,
        width='stretch',
        height=min(45 * len(df_display) + 40, 600)
    )

    csv = prepare_export_data(df_table).to_csv()
    st.download_button(
        label="📥 Exportar DFC",
        data=csv,
        file_name=f"dfc_{key_prefix}.csv",
        mime="text/csv",
        key=f'download_dfc_{key_prefix}'
    )


def build_pl_table(df_company: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói a tabela P&L pivotada.
    Linhas = contas DRE + indicadores
    Colunas = trimestres ordenados (esquerda = mais antigo)
    """
    # Deduplicar por trimestre — manter o registro mais recente se houver duplicata
    df_sorted = (
        df_company
        .sort_values('Data_Trimestre')
        .drop_duplicates(subset=['Data_Trimestre'], keep='last')
        .reset_index(drop=True)
    )

    # Labels de trimestre
    if 'Trimestre' in df_sorted.columns:
        trimestres = df_sorted['Trimestre'].astype(str).tolist()
    else:
        trimestres = (
            df_sorted['Data_Trimestre'].dt.year.astype(str) + 'Q' +
            df_sorted['Data_Trimestre'].dt.quarter.astype(str)
        ).tolist()

    # Garantir unicidade dos labels (edge case: mesmo trimestre, datas diferentes)
    seen = {}
    unique_trimestres = []
    for t in trimestres:
        count = seen.get(t, 0)
        seen[t] = count + 1
        unique_trimestres.append(f"{t}.{count}" if count > 0 else t)
    trimestres = unique_trimestres

    available_cols = set(df_sorted.columns)
    rows = {}

    # Contas DRE
    for display_name, col_name, is_subtotal in DRE_ACCOUNTS:
        if col_name in available_cols:
            values = df_sorted[col_name].tolist()
            rows[display_name] = values

    # Separador
    rows[SEPARATOR_LABEL] = [None] * len(trimestres)

    # Pré-calcular Lucro Líquido LTM (soma rolling 4 trimestres) para ROE/ROA
    ll_series = df_sorted['Lucro Líquido'].values if 'Lucro Líquido' in df_sorted.columns else None
    at_series = df_sorted['Ativo Total'].values if 'Ativo Total' in df_sorted.columns else None

    def _ll_ltm(idx):
        if ll_series is None:
            return None
        start = max(0, idx - 3)
        window = ll_series[start:idx + 1]
        if len(window) == 0 or all(pd.isna(v) for v in window):
            return None
        return float(np.nansum(window))

    def _at_avg(idx):
        if at_series is None:
            return None
        start = max(0, idx - 3)
        window = at_series[start:idx + 1]
        valid = [v for v in window if not pd.isna(v)]
        return float(np.mean(valid)) if valid else None

    # Indicadores
    for display_name, indicator_key, fmt in INDICATORS:
        values = []
        for i, (_, row) in enumerate(df_sorted.iterrows()):
            if indicator_key == 'roe':
                # ROE anualizado (LTM): Lucro Líquido LTM / PL
                ll_ltm = _ll_ltm(i)
                pl = row.get('Patrimônio Líquido')
                if ll_ltm is not None and pd.notna(pl) and float(pl) != 0:
                    val = ll_ltm / float(pl)
                else:
                    val = None
            elif indicator_key == 'roa':
                # ROA anualizado (LTM): Lucro Líquido LTM / Ativo Total médio
                ll_ltm = _ll_ltm(i)
                at_avg = _at_avg(i)
                if ll_ltm is not None and at_avg is not None and at_avg != 0:
                    val = ll_ltm / at_avg
                else:
                    val = None
            else:
                val = _calc_indicator(row, indicator_key)
            values.append(val)

        if any(v is not None for v in values):
            rows[display_name] = values

    df_table = pd.DataFrame(rows, index=trimestres).T
    df_table.index.name = 'Conta'

    return df_table


def render_pl_table(df_table: pd.DataFrame, key_prefix: str):
    """Renderiza uma tabela P&L formatada com estilos."""
    if df_table.empty:
        st.info("Nenhum dado disponível para exibir.")
        return

    # Aviso de dados parciais
    has_receita = 'Receita Líquida' in df_table.index
    if not has_receita:
        st.caption(
            "💡 **Dados parciais**: Receita Líquida, CPV, Lucro Bruto, Despesas e EBIT "
            "não estão disponíveis. Para o DRE completo, reprocesse o pipeline com as "
            "contas 3.01–3.05 habilitadas."
        )

    # Formatar valores para exibição
    df_display = df_table.copy().astype(object)

    for row_name in df_display.index:
        for col in df_display.columns:
            val = _to_scalar(df_table.loc[row_name, col])
            df_display.loc[row_name, col] = format_pl_value(val, row_name)

    # Estilos
    def _highlight_rows(row):
        row_name = row.name
        if row_name in SUBTOTAL_ROWS:
            return ['font-weight: bold; background-color: rgba(59, 130, 246, 0.10)'] * len(row)
        elif row_name.startswith('─'):
            return ['border-top: 2px solid #555; font-size: 2px; color: transparent'] * len(row)
        return [''] * len(row)

    def _color_negatives(val):
        if isinstance(val, str) and val.strip().startswith('-'):
            return 'color: #ef4444'
        return ''

    styled = df_display.style \
        .apply(_highlight_rows, axis=1) \
        .applymap(_color_negatives)

    st.dataframe(
        styled,
        width='stretch',
        height=min(45 * len(df_display) + 40, 800)
    )

    # Export específico da tabela
    csv = prepare_export_data(df_table).to_csv()
    st.download_button(
        label=f"📥 Exportar P&L",
        data=csv,
        file_name=f"pl_{key_prefix}.csv",
        mime="text/csv",
        key=f'download_pl_{key_prefix}'
    )


# ========================== PÁGINA PRINCIPAL ==========================

st.title("📋 P&L — Demonstrativo de Resultados")
st.markdown("Visualize o DRE completo por empresa, com todos os períodos lado a lado.")

# Filtros da sidebar
filters = render_sidebar_filters()

try:
    df_base = load_and_prepare_base(PARQUET_BASE_FILE)
    df_filtered = apply_filters(df_base, filters)

    if len(df_filtered) == 0:
        st.warning("⚠️ Nenhum dado disponível com os filtros atuais.")
        st.stop()

    # ========================== SELETORES P&L ==========================
    st.header("🔎 Seleção de Empresas / Setores")

    col_sel1, col_sel2 = st.columns(2)

    all_tickers_pl = sorted(df_filtered['Ticker'].dropna().astype(str).unique().tolist())
    all_sectors_pl = sorted(df_filtered['Tipo'].dropna().astype(str).unique().tolist())

    with col_sel1:
        selected_sectors_pl = st.multiselect(
            "Filtrar por Setores:",
            options=all_sectors_pl,
            default=[],
            key='pl_sector_filter',
            help="Selecione um ou mais setores para filtrar empresas"
        )

    # Filtrar tickers por setor
    if selected_sectors_pl:
        df_sector_filtered = df_filtered[df_filtered['Tipo'].isin(selected_sectors_pl)]
        available_tickers_pl = sorted(
            df_sector_filtered['Ticker'].dropna().astype(str).unique().tolist()
        )
    else:
        df_sector_filtered = df_filtered
        available_tickers_pl = all_tickers_pl

    with col_sel2:
        selected_tickers_pl = st.multiselect(
            "Selecionar Empresas:",
            options=available_tickers_pl,
            default=[],
            key='pl_ticker_filter',
            help="Selecione uma ou mais empresas para ver o P&L"
        )

    if not selected_tickers_pl and not selected_sectors_pl:
        st.info(
            "👆 Selecione pelo menos uma **empresa** ou **setor** acima "
            "para visualizar o P&L."
        )
        st.stop()

    st.divider()

    # ========================== CONSTRUIR E RENDERIZAR TABELAS ==========================

    # Determinar modo: agregado por setor ou individual
    show_aggregated = bool(selected_sectors_pl) and not selected_tickers_pl

    if show_aggregated:
        # ---- VISÃO AGREGADA POR SETOR ----
        st.header("📊 P&L Agregado por Setor")

        for sector in selected_sectors_pl:
            st.subheader(f"🏭 {sector}")

            df_sector_data = df_sector_filtered[df_sector_filtered['Tipo'] == sector]

            if len(df_sector_data) == 0:
                st.info(f"Sem dados para o setor {sector}")
                continue

            # Agregar por trimestre (soma)
            numeric_cols_for_agg = [col for col in [
                # DRE
                'Receita Líquida', 'CPV', 'Lucro Bruto', 'Despesas Operacionais',
                'EBIT', 'D&A', 'EBITDA', 'Resultado Financeiro', 'IR', 'Lucro Líquido',
                # Balanço
                'Ativo Total', 'Ativo Circulante', 'Caixa', 'Aplicações Financeiras',
                'Contas a Receber', 'Estoques', 'Ativo Não Circulante',
                'Imobilizado', 'Intangível',
                'Passivo Circulante', 'Passivo Não Circulante',
                'Dívida Bruta', 'Dívida Líquida', 'Patrimônio Líquido',
            ] if col in df_sector_data.columns]

            df_agg = df_sector_data.groupby('Data_Trimestre')[numeric_cols_for_agg].sum().reset_index()

            if 'Data_Trimestre' in df_agg.columns:
                df_agg['Trimestre'] = (
                    df_agg['Data_Trimestre'].dt.year.astype(str) + 'Q' +
                    df_agg['Data_Trimestre'].dt.quarter.astype(str)
                )

            n_empresas = df_sector_data.groupby('Data_Trimestre')['Ticker'].nunique().values
            st.caption(f"📊 Agregação de ~{int(np.median(n_empresas)) if len(n_empresas) > 0 else 0} empresas por trimestre")

            setor_key = f"setor_{sector.replace(' ', '_')}"

            tab_pl, tab_bp, tab_dfc = st.tabs(["📋 DRE / P&L", "📘 Balanço Patrimonial", "💰 Fluxo de Caixa"])
            with tab_pl:
                table = build_pl_table(df_agg)
                render_pl_table(table, setor_key)
            with tab_bp:
                bp_table = build_bp_table(df_agg)
                render_bp_table(bp_table, setor_key)
            with tab_dfc:
                dfc_table = build_dfc_table(df_agg)
                render_dfc_table(dfc_table, setor_key)

    else:
        # ---- VISÃO POR EMPRESA ----
        companies_to_show = selected_tickers_pl if selected_tickers_pl else available_tickers_pl

        MAX_COMPANIES = 10
        if len(companies_to_show) > MAX_COMPANIES:
            st.warning(
                f"⚠️ {len(companies_to_show)} empresas selecionadas. "
                f"Mostrando as primeiras {MAX_COMPANIES}. Refine os filtros."
            )
            companies_to_show = companies_to_show[:MAX_COMPANIES]

        if len(companies_to_show) == 1:
            # Empresa única — tabs DRE / Balanço
            ticker = companies_to_show[0]
            df_company = filter_by_tickers(df_sector_filtered, [ticker])

            if len(df_company) == 0:
                st.warning(f"Sem dados para {ticker}")
            else:
                empresa_nome = df_company.iloc[0].get('Empresa', ticker)
                st.header(f"📊 {ticker} — {empresa_nome}")

                tab_pl, tab_bp, tab_dfc = st.tabs(["📋 DRE / P&L", "📘 Balanço Patrimonial", "💰 Fluxo de Caixa"])
                with tab_pl:
                    table = build_pl_table(df_company)
                    render_pl_table(table, ticker)
                with tab_bp:
                    bp_table = build_bp_table(df_company)
                    render_bp_table(bp_table, ticker)
                with tab_dfc:
                    dfc_table = build_dfc_table(df_company)
                    render_dfc_table(dfc_table, ticker)

        elif len(companies_to_show) > 1:
            # Múltiplas empresas — tabs por empresa, cada uma com sub-tabs DRE/BP
            st.header("📊 P&L + Balanço por Empresa")
            company_tabs = st.tabs(companies_to_show)

            for company_tab, ticker in zip(company_tabs, companies_to_show):
                with company_tab:
                    df_company = filter_by_tickers(df_sector_filtered, [ticker])

                    if len(df_company) == 0:
                        st.info(f"Sem dados para {ticker}")
                        continue

                    empresa_nome = df_company.iloc[0].get('Empresa', ticker)
                    st.subheader(f"{ticker} — {empresa_nome}")

                    tab_pl, tab_bp, tab_dfc = st.tabs(["📋 DRE / P&L", "📘 Balanço Patrimonial", "💰 Fluxo de Caixa"])
                    with tab_pl:
                        table = build_pl_table(df_company)
                        render_pl_table(table, ticker)
                    with tab_bp:
                        bp_table = build_bp_table(df_company)
                        render_bp_table(bp_table, ticker)
                    with tab_dfc:
                        dfc_table = build_dfc_table(df_company)
                        render_dfc_table(dfc_table, ticker)
        else:
            st.warning("Nenhuma empresa encontrada com os filtros selecionados.")

    # Export geral
    render_export_buttons(df_filtered)

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(traceback.format_exc())
