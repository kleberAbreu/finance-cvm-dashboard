"""
Dashboard Streamlit para Análise Financeira CVM.

Aplicação multipage para visualização e análise de dados financeiros
de empresas brasileiras (CVM + Yahoo Finance).
"""
import streamlit as st
import yaml
from pathlib import Path

# Configuração da página — deve ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Dashboard CVM - Análise Financeira",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# AUTENTICAÇÃO
# =============================================================================
import streamlit_authenticator as stauth

AUTH_CONFIG_PATH = Path(__file__).parent / "auth_config.yaml"

try:
    with open(AUTH_CONFIG_PATH) as f:
        auth_config = yaml.load(f, Loader=yaml.SafeLoader)
except FileNotFoundError:
    st.error("❌ Arquivo auth_config.yaml não encontrado. Verifique a instalação.")
    st.stop()

authenticator = stauth.Authenticate(
    auth_config["credentials"],
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
)

# Tela de login
name, authentication_status, username = authenticator.login(
    fields={
        "Form name": "🔐 Dashboard CVM — Login",
        "Username": "Usuário",
        "Password": "Senha",
        "Login": "Entrar",
    },
    location="main",
)

# Bloqueia acesso se não autenticado
if authentication_status is False:
    st.error("⛔ Usuário ou senha incorretos.")
    st.stop()

if authentication_status is None:
    st.info("👆 Insira suas credenciais para acessar o dashboard.")
    st.stop()

# =============================================================================
# APP PRINCIPAL (só chega aqui se autenticado)
# =============================================================================

# Botão de logout na sidebar
with st.sidebar:
    st.markdown(f"👤 **{name}**")
    authenticator.logout("Sair", location="sidebar")
    st.divider()

# CSS customizado
def load_custom_css():
    """Carrega CSS customizado do arquivo externo."""
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
    from config.settings import PARQUET_BASE_FILE

    try:
        summary = get_data_summary(PARQUET_BASE_FILE)

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
