"""
Página 7: Pipeline Execution - Execução do Pipeline CVM (Incremental)

O pipeline completo deve ser executado pelo terminal local para evitar longos
processamentos dentro da UI.
"""
import streamlit as st
from src.publication import is_public_demo

if is_public_demo():
    st.info("Atualização de dados disponível apenas no ambiente local do mantenedor.")
    st.stop()

from datetime import datetime
from src.data.pipeline_runner import PipelineRunner
from src.data.incremental_pipeline import get_incremental_info
from src.data.loader import get_data_source_info
from config.settings import PARQUET_BASE_FILE

st.set_page_config(page_title="Pipeline Execution - Dashboard CVM", page_icon="⚙️", layout="wide")

st.title("⚙️ Execução do Pipeline")

st.markdown("""
Execute o pipeline incremental para adicionar novos trimestres à base completa
gerada localmente. A amostra pública não é atualizada por esta tela.
""")

# =============================================================================
# PIPELINE INCREMENTAL
# =============================================================================

st.header("📊 Pipeline Incremental")

# Verificar informações incrementais
source_info = get_data_source_info()
info = get_incremental_info(PARQUET_BASE_FILE)

if source_info['using_sample']:
    st.info("""
    ℹ️ **Você está usando a amostra pública.**

    Para habilitar o incremental, gere primeiro a base completa:

    ```bash
    python run_pipeline.py --inicio 2018 --fim 2025
    ```
    """)
    run_incremental = False
elif info['can_increment']:
    st.markdown(f"""
    **Processa apenas novos trimestres:**
    - ⏱️ Tempo estimado: ~{len(info['next_quarters']) * 5} minutos
    - 📊 Dados: {len(info['next_quarters'])} trimestre(s) novo(s)
    - ✅ Rápido e seguro

    **Último processado:** {info['last_quarter']}
    """)

    with st.expander("Ver trimestres a processar"):
        for year, quarter in info['next_quarters']:
            st.write(f"- Q{quarter} {year}")

    run_incremental = st.button("▶️ Executar Pipeline Incremental",
                                key='run_inc_btn',
                                width='stretch',
                                type='primary')
else:
    if info['exists']:
        st.success("""
        ✅ **Dados já atualizados!**

        Nenhum trimestre novo disponível para processar.
        """)
    else:
        st.warning("""
        ⚠️ **Nenhum arquivo de dados encontrado**

        Execute o pipeline completo pelo terminal local antes de usar o incremental.
        """)

    run_incremental = False

st.divider()

# =============================================================================
# NOTA SOBRE PIPELINE COMPLETO
# =============================================================================

st.info("""
💡 **Pipeline Completo (reprocessamento total)**

Execute pelo terminal na raiz do projeto:

```bash
python run_pipeline.py --inicio 2018 --fim 2025
```

Use quando precisar criar a base pela primeira vez ou reprocessar tudo do zero.
""")

st.divider()

# =============================================================================
# EXECUÇÃO DO PIPELINE INCREMENTAL
# =============================================================================

if 'pipeline_running' not in st.session_state:
    st.session_state.pipeline_running = False

if run_incremental:
    if st.session_state.pipeline_running:
        st.warning("⚠️ Pipeline já está em execução!")
        st.stop()

    st.session_state.pipeline_running = True

    # Containers para UI
    status_container = st.container()
    progress_container = st.container()
    log_container = st.container()

    with status_container:
        st.info("🚀 **Pipeline Incremental Iniciado**")
        st.markdown(f"*Início: {datetime.now().strftime('%H:%M:%S')}*")

    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()

    with log_container:
        log_area = st.expander("📋 Log Detalhado", expanded=True)
        log_messages = []

    # Callback para atualizar progresso
    def update_progress(pct: float, message: str):
        progress_bar.progress(min(pct, 1.0))
        status_text.text(message)

        timestamp = datetime.now().strftime('%H:%M:%S')
        log_messages.append(f"[{timestamp}] {message}")

        with log_area:
            st.text('\n'.join(log_messages[-20:]))  # Últimas 20 mensagens

    try:
        info = get_incremental_info(PARQUET_BASE_FILE)

        if not info['can_increment']:
            st.warning("Nenhum trimestre novo disponível")
            st.session_state.pipeline_running = False
            st.stop()

        runner = PipelineRunner(
            progress_callback=update_progress
        )

        update_progress(0.0, "Inicializando pipeline incremental...")

        result_df = runner.run_incremental_pipeline(info['next_quarters'])

        if not result_df.empty:
            with status_container:
                st.success(f"""
                ✅ **Pipeline Incremental Finalizado!**

                - 📊 {len(result_df):,} novos registros
                - 📈 {len(info['next_quarters'])} trimestre(s) adicionado(s)
                - ⏱️ Concluído em: {datetime.now().strftime('%H:%M:%S')}

                **Arquivo atualizado:** `{PARQUET_BASE_FILE}`
                """)

            st.balloons()
        else:
            st.warning("⚠️ Nenhum dado novo foi processado")

    except Exception as e:
        with status_container:
            st.error(f"❌ **Erro durante execução:**\n\n{str(e)}")

        import traceback
        with log_area:
            st.code(traceback.format_exc())

    finally:
        st.session_state.pipeline_running = False

        # Botão para voltar
        if st.button("🔄 Executar Novamente", key='restart_btn'):
            st.rerun()

# =============================================================================
# AJUDA
# =============================================================================

with st.expander("❓ Ajuda"):
    st.markdown("""
    ### Pipeline Incremental

    **Use quando:**
    - ✅ Quer adicionar novos trimestres à base existente
    - ✅ Faz atualizações regulares (a cada 3 meses)
    - ✅ Quer economizar tempo

    **Tempo estimado:** ~5 minutos por trimestre

    ---

    ### Calendário de Divulgação CVM

    | Trimestre | Divulgação até | Processe a partir de |
    |-----------|----------------|----------------------|
    | Q1 (Jan-Mar) | Maio | Junho |
    | Q2 (Abr-Jun) | Agosto | Setembro |
    | Q3 (Jul-Set) | Novembro | Dezembro |
    | Q4 (Out-Dez) | Março (ano seguinte) | Abril |

    Execute o pipeline incremental ~1 mês após o fim do trimestre.

    ---

    ### Pipeline Completo

    Para reprocessar tudo do zero, execute no terminal:

    ```bash
    python run_pipeline.py
    python run_pipeline.py --inicio 2020
    ```
    """)
