"""
Dashboard Streamlit para Análise Financeira CVM.

Aplicação multipage para visualização e análise de dados financeiros
de empresas brasileiras (CVM + Yahoo Finance).
"""
import streamlit as st
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Dashboard CVM - Análise Financeira",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
def load_custom_css():
    """Carrega CSS customizado do arquivo externo."""
    # CSS crítico inline para sidebar e privacidade (garante carregamento imediato)
    critical_css = """
    <style>
        /* REMOVER BOTÃO DE DEPLOY - PROJETO PRIVADO */
        [data-testid="stToolbar"],
        [data-testid="stDeployButton"],
        [data-testid="stShareButton"],
        button[kind="header"] {
            display: none !important;
        }
        header[data-testid="stHeader"] > div:first-child {
            display: none !important;
        }

        /* SIDEBAR ESCURA - CRÍTICO */
        [data-testid="stSidebar"] {
            background-color: #1a1d24 !important;
        }
        [data-testid="stSidebar"] * {
            color: #fafafa !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #fafafa !important;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] select {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
    </style>
    """
    st.markdown(critical_css, unsafe_allow_html=True)

    # Carregar CSS completo do arquivo
    css_file = Path(__file__).parent / "assets" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)

load_custom_css()

# Título principal
st.title("📊 Dashboard de Análise Financeira - CVM")
st.markdown("**Análise de valuation de empresas brasileiras** (Dados CVM + Yahoo Finance)")

# Sidebar com filtros universais
from src.components.sidebar import render_sidebar_filters

filters = render_sidebar_filters()

# Informações sobre navegação
st.info("""
👈 **Use a sidebar para:**
- Filtrar dados por período, empresas e setores
- Ajustar ranges de métricas financeiras
- Exportar dados

📄 **Navegue pelas páginas usando o menu lateral:**
- **Overview**: Visão geral do mercado
- **Company Analysis**: Análise individual e comparação de empresas
- **Sector Comparison**: Benchmarking setorial
- **Screener**: Filtro e ranqueamento customizado
- **Time Series**: Análise de tendências temporais
- **Correlations**: Análise de correlações entre métricas
""")

# Informações sobre os dados
with st.expander("ℹ️ Sobre os Dados"):
    from src.data.loader import get_data_summary
    from config.settings import DEFAULT_EXCEL

    try:
        summary = get_data_summary(DEFAULT_EXCEL)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total de Registros", f"{summary['total_records']:,}")

        with col2:
            st.metric("Empresas", summary['total_companies'])

        with col3:
            st.metric("Setores", summary['total_sectors'])

        with col4:
            date_range = summary['date_range']
            if date_range['min'] and date_range['max']:
                st.metric("Período", f"{date_range['min'].year} - {date_range['max'].year}")

        # Qualidade dos dados
        st.subheader("Qualidade dos Dados")

        quality = summary['quality']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Células Totais", f"{quality['total_cells']:,}")

        with col2:
            st.metric("Células com Dados Faltando", f"{quality['missing_cells']:,}")

        with col3:
            st.metric("% Dados Faltando", f"{quality['missing_percent']:.2f}%")

        if quality['infinite_values']:
            st.warning(f"⚠️ {quality['infinite_total']} valores infinitos encontrados")

    except Exception as e:
        st.error(f"Erro ao carregar resumo dos dados: {str(e)}")

# Footer
st.divider()
st.caption("💡 **Dica:** Use o filtro 'Top N por Market Cap' na sidebar para uma análise rápida das maiores empresas")
st.caption("📈 Dados: CVM (Comissão de Valores Mobiliários) + Yahoo Finance")
