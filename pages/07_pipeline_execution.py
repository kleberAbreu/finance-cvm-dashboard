"""
Página 7: Pipeline Execution - Execução do Pipeline CVM
"""
import streamlit as st
from datetime import datetime
from pathlib import Path
from src.data.pipeline_runner import PipelineRunner
from src.data.incremental_pipeline import get_incremental_info
from config.settings import PARQUET_BASE_FILE

st.set_page_config(page_title="Pipeline Execution - Dashboard CVM", page_icon="⚙️", layout="wide")

st.title("⚙️ Execução do Pipeline")

st.markdown("""
Execute o pipeline CVM para processar dados da CVM e enriquecer com Yahoo Finance.
Escolha entre **modo completo** (processa tudo) ou **modo incremental** (apenas novos trimestres).
""")

# =============================================================================
# SELEÇÃO DE MODO
# =============================================================================

st.header("🎯 Selecione o Modo de Execução")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pipeline Completo")
    st.markdown("""
    **Processa tudo do zero:**
    - ⏱️ Tempo: 3-4 horas
    - 📊 Dados: 2015-2025 (completo)
    - ✅ Garante consistência total
    - 🎯 Use para primeira execução
    """)

    run_full = st.button("▶️ Executar Pipeline Completo",
                         key='run_full_btn',
                         use_container_width=True,
                         type='primary')

with col2:
    st.subheader("Pipeline Incremental")

    # Verificar informações incrementais
    info = get_incremental_info(PARQUET_BASE_FILE)

    if info['can_increment']:
        st.markdown(f"""
        **Processa apenas novos trimestres:**
        - ⏱️ Tempo: ~{len(info['next_quarters']) * 5} minutos
        - 📊 Dados: {len(info['next_quarters'])} trimestre(s) novo(s)
        - ✅ Muito mais rápido
        - 🎯 Use para atualizações

        **Último processado:** {info['last_quarter']}
        """)

        with st.expander("Ver trimestres a processar"):
            for year, quarter in info['next_quarters']:
                st.write(f"- Q{quarter} {year}")

        run_incremental = st.button("▶️ Executar Pipeline Incremental",
                                    key='run_inc_btn',
                                    use_container_width=True,
                                    type='primary')
    else:
        if info['exists']:
            st.success("""
            ✅ **Dados já atualizados!**

            Nenhum trimestre novo disponível para processar.
            """)
        else:
            st.warning("""
            ⚠️ **Nenhum Excel encontrado**

            Execute o pipeline completo primeiro.
            """)

        run_incremental = False

st.divider()

# =============================================================================
# CONFIGURAÇÃO (apenas para modo completo)
# =============================================================================

if 'pipeline_running' not in st.session_state:
    st.session_state.pipeline_running = False

# Configurações para pipeline completo
with st.expander("⚙️ Configurações Avançadas (Pipeline Completo)"):
    col1, col2 = st.columns(2)

    with col1:
        ano_inicio = st.number_input(
            "Ano Início",
            min_value=2010,
            max_value=2025,
            value=2015,
            key='config_ano_inicio'
        )

    with col2:
        ano_fim = st.number_input(
            "Ano Fim",
            min_value=2010,
            max_value=2026,
            value=2025,
            key='config_ano_fim'
        )

    if ano_inicio > ano_fim:
        st.error("⚠️ Ano de início deve ser menor ou igual ao ano fim")

st.divider()

# =============================================================================
# EXECUÇÃO DO PIPELINE
# =============================================================================

if run_full or run_incremental:
    if st.session_state.pipeline_running:
        st.warning("⚠️ Pipeline já está em execução!")
        st.stop()

    st.session_state.pipeline_running = True

    # Containers para UI
    status_container = st.container()
    progress_container = st.container()
    log_container = st.container()

    with status_container:
        st.info(f"🚀 **Pipeline {'Completo' if run_full else 'Incremental'} Iniciado**")
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
        if run_full:
            # Pipeline Completo
            runner = PipelineRunner(
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
                progress_callback=update_progress
            )

            update_progress(0.0, "Inicializando pipeline completo...")

            result_df = runner.run_full_pipeline()

            if not result_df.empty:
                with status_container:
                    st.success(f"""
                    ✅ **Pipeline Completo Finalizado!**

                    - 📊 {len(result_df):,} registros processados
                    - 🏢 {result_df['Ticker'].nunique()} empresas
                    - 📅 Período: {result_df['DT_FIM_EXERC'].min().strftime('%Y-%m-%d')} a {result_df['DT_FIM_EXERC'].max().strftime('%Y-%m-%d')}
                    - ⏱️ Concluído em: {datetime.now().strftime('%H:%M:%S')}

                    **Arquivo gerado:** `pipeline_cvm_final/outputs/Valuation_Final_{datetime.now().strftime('%Y%m%d')}.xlsx`
                    """)

                st.balloons()
            else:
                st.error("❌ Pipeline falhou - nenhum dado processado")

        elif run_incremental:
            # Pipeline Incremental
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
# HISTÓRICO DE EXECUÇÕES (placeholder)
# =============================================================================

st.divider()

st.header("📜 Histórico de Execuções")

st.info("""
💡 **Funcionalidade futura:**

Aqui será exibido o histórico de execuções do pipeline com:
- Data/hora de execução
- Modo (completo/incremental)
- Duração
- Status (sucesso/erro)
- Link para arquivo gerado
""")

# =============================================================================
# AJUDA
# =============================================================================

with st.expander("❓ Ajuda - Quando usar cada modo"):
    st.markdown("""
    ### Pipeline Completo

    **Use quando:**
    - ✅ É sua primeira execução (não tem Excel)
    - ✅ Quer reprocessar tudo do zero
    - ✅ Suspeita de dados corrompidos
    - ✅ Mudou configurações importantes

    **Tempo estimado:** 3-4 horas

    ---

    ### Pipeline Incremental

    **Use quando:**
    - ✅ Já tem Excel atualizado
    - ✅ Quer apenas adicionar novos trimestres
    - ✅ Faz atualizações regulares (a cada 3 meses)
    - ✅ Quer economizar tempo

    **Tempo estimado:** ~5 minutos por trimestre

    ---

    ### Calendário de Divulgação

    | Trimestre | Divulgação até | Processe a partir de |
    |-----------|----------------|----------------------|
    | Q1 (Jan-Mar) | Maio | Junho |
    | Q2 (Abr-Jun) | Agosto | Setembro |
    | Q3 (Jul-Set) | Novembro | Dezembro |
    | Q4 (Out-Dez) | Março (ano seguinte) | Abril |

    Execute o pipeline incremental ~1 mês após o fim do trimestre.
    """)
