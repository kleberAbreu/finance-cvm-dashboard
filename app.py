"""
Dashboard Streamlit para Análise Financeira CVM.

Aplicação multipage para visualização e análise de dados financeiros
de empresas brasileiras (CVM + Yahoo Finance).
"""
import os
import streamlit as st
from pathlib import Path

# Configuração da página — deve ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Dashboard CVM - Análise Financeira",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

AUTH_CONFIG_PATH = Path(__file__).parent / "auth_config.yaml"


def _is_truthy(value: object) -> bool:
    """Interpreta valores comuns de configuracao booleana."""
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _has_local_secrets_file() -> bool:
    secrets_paths = [
        Path.home() / ".streamlit" / "secrets.toml",
        Path(__file__).parent / ".streamlit" / "secrets.toml",
    ]
    return any(path.exists() for path in secrets_paths)


def _secrets_get(key: str, default=None):
    if not _has_local_secrets_file():
        return default
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def auth_is_enabled() -> bool:
    """Ativa login apenas em deploys privados explicitamente configurados."""
    env_enabled = _is_truthy(os.getenv("CVM_DASHBOARD_AUTH", ""))
    secrets_enabled = _is_truthy(_secrets_get("auth_enabled", False))
    return env_enabled or secrets_enabled


def load_auth_config():
    """Carrega configuracao opcional do streamlit-authenticator."""
    secrets_config = _secrets_get("auth_config")
    if secrets_config:
        return dict(secrets_config)

    if not AUTH_CONFIG_PATH.exists():
        return None

    try:
        import yaml
    except ImportError:
        st.error("PyYAML precisa estar instalado para usar autenticação opcional.")
        st.stop()

    with open(AUTH_CONFIG_PATH) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)


def require_auth_if_enabled():
    """Bloqueia acesso somente quando o modo privado estiver habilitado."""
    if not auth_is_enabled():
        return None, None

    try:
        import streamlit_authenticator as stauth
    except ImportError:
        st.error("streamlit-authenticator precisa estar instalado para usar autenticação opcional.")
        st.stop()

    auth_config = load_auth_config()
    if not auth_config:
        st.error("Autenticação habilitada, mas auth_config.yaml ou st.secrets['auth_config'] não foi configurado.")
        st.stop()

    authenticator = stauth.Authenticate(
        auth_config["credentials"],
        auth_config["cookie"]["name"],
        auth_config["cookie"]["key"],
        auth_config["cookie"]["expiry_days"],
    )

    try:
        result = authenticator.login(
            fields={
                "Form name": "🔐 Dashboard CVM - Login",
                "Username": "Usuário",
                "Password": "Senha",
                "Login": "Entrar",
            },
            location="main",
        )
        if result is not None:
            name, authentication_status, _username = result
        else:
            authentication_status = st.session_state.get("authentication_status")
            name = st.session_state.get("name")
    except Exception:
        authentication_status = st.session_state.get("authentication_status")
        name = st.session_state.get("name")

    if authentication_status is False:
        st.error("Usuário ou senha incorretos.")
        st.stop()

    if authentication_status is None:
        st.info("Insira suas credenciais para acessar o dashboard.")
        st.stop()

    return authenticator, name


authenticator, authenticated_name = require_auth_if_enabled()

if authenticator:
    with st.sidebar:
        st.markdown(f"👤 **{authenticated_name}**")
        authenticator.logout("Sair", location="sidebar")
        st.divider()

# CSS customizado
def load_custom_css():
    """Carrega CSS customizado do arquivo externo."""
    critical_css = """
    <style>
        /* Ajustes de toolbar em deploys hospedados */
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
- **P&L**: Demonstrativo de Resultados (DRE) por empresa
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
