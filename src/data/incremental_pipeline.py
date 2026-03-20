"""
Pipeline incremental para processar apenas novos trimestres.
Evita reprocessar dados históricos já existentes.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import streamlit as st
from typing import Tuple, Optional


def get_latest_quarter_from_parquet(parquet_path: Path) -> Optional[Tuple[int, int]]:
    """
    Identifica o último trimestre processado no Parquet.

    Args:
        parquet_path: Caminho do arquivo Parquet existente

    Returns:
        Tuple (ano, trimestre) do último dado processado, ou None se não existir
    """
    if not parquet_path.exists():
        return None

    try:
        df = pd.read_parquet(parquet_path, engine='pyarrow', columns=['DT_FIM_EXERC'])

        if 'DT_FIM_EXERC' not in df.columns:
            return None

        # Converter para datetime (Parquet geralmente já mantém o tipo correto)
        df['DT_FIM_EXERC'] = pd.to_datetime(df['DT_FIM_EXERC'], errors='coerce')

        # Pegar data mais recente
        latest_date = df['DT_FIM_EXERC'].max()

        if pd.isna(latest_date):
            return None

        # Extrair ano e trimestre
        year = latest_date.year
        quarter = (latest_date.month - 1) // 3 + 1

        return (year, quarter)

    except Exception as e:
        st.error(f"Erro ao ler Parquet existente: {str(e)}")
        return None


def calculate_quarters_to_process(last_year: int, last_quarter: int,
                                  target_year: int, target_quarter: int) -> list:
    """
    Calcula quais trimestres precisam ser processados.

    Args:
        last_year: Ano do último trimestre processado
        last_quarter: Trimestre do último processado (1-4)
        target_year: Ano alvo final
        target_quarter: Trimestre alvo final (1-4)

    Returns:
        Lista de tuples (ano, trimestre) a processar
    """
    quarters = []

    current_year = last_year
    current_quarter = last_quarter + 1  # Começar do próximo

    while True:
        # Ajustar se passar de Q4
        if current_quarter > 4:
            current_quarter = 1
            current_year += 1

        # Verificar se chegou ao alvo
        if current_year > target_year:
            break
        if current_year == target_year and current_quarter > target_quarter:
            break

        quarters.append((current_year, current_quarter))

        current_quarter += 1

    return quarters


def get_quarter_date(year: int, quarter: int) -> datetime:
    """
    Retorna a data final de um trimestre.

    Args:
        year: Ano
        quarter: Trimestre (1-4)

    Returns:
        Datetime do último dia do trimestre
    """
    month = quarter * 3
    day = 31 if month in [3, 12] else 30

    return datetime(year, month, day)


def merge_incremental_data(existing_parquet: Path, new_df: pd.DataFrame) -> pd.DataFrame:
    """
    Faz merge dos novos dados com o Parquet existente.

    Args:
        existing_parquet: Caminho do Parquet existente
        new_df: DataFrame com novos dados processados

    Returns:
        DataFrame combinado (histórico + novos)
    """
    # Carregar dados existentes
    df_existing = pd.read_parquet(existing_parquet)

    # Concatenar
    df_combined = pd.concat([df_existing, new_df], ignore_index=True)

    # Remover duplicatas (por CNPJ + Data)
    if 'CNPJ_CIA' in df_combined.columns and 'DT_FIM_EXERC' in df_combined.columns:
        df_combined = df_combined.drop_duplicates(
            subset=['CNPJ_CIA', 'DT_FIM_EXERC'],
            keep='last'
        )

    # Ordenar por data
    if 'DT_FIM_EXERC' in df_combined.columns:
        df_combined = df_combined.sort_values(['CNPJ_CIA', 'DT_FIM_EXERC'])

    return df_combined


def get_incremental_info(parquet_path: Path) -> dict:
    """
    Retorna informações sobre processamento incremental.

    Args:
        parquet_path: Caminho do Parquet existente

    Returns:
        Dicionário com informações
    """
    info = {
        'exists': parquet_path.exists(),
        'last_quarter': None,
        'last_date': None,
        'quarters_behind': 0,
        'can_increment': False
    }

    if not info['exists']:
        return info

    last_q = get_latest_quarter_from_parquet(parquet_path)

    if last_q:
        year, quarter = last_q
        info['last_quarter'] = f"Q{quarter} {year}"
        info['last_date'] = get_quarter_date(year, quarter)

        # Calcular quantos trimestres está atrasado
        now = datetime.now()
        current_year = now.year
        current_quarter = (now.month - 1) // 3 + 1

        # Considerar que dados do trimestre atual só ficam disponíveis no trimestre seguinte
        if now.month <= 3:
            current_quarter = 4
            current_year -= 1
        else:
            current_quarter -= 1

        quarters_to_process = calculate_quarters_to_process(
            year, quarter, current_year, current_quarter
        )

        info['quarters_behind'] = len(quarters_to_process)
        info['can_increment'] = len(quarters_to_process) > 0
        info['next_quarters'] = quarters_to_process

    return info


def estimate_incremental_time(num_quarters: int) -> str:
    """
    Estima tempo de processamento incremental.

    Args:
        num_quarters: Número de trimestres a processar

    Returns:
        String com estimativa (ex: "15-20 min")
    """
    # Estimativa: ~5 minutos por trimestre
    minutes_per_quarter = 5
    total_minutes = num_quarters * minutes_per_quarter

    if total_minutes < 60:
        return f"{total_minutes}-{total_minutes + 10} min"
    else:
        hours = total_minutes / 60
        return f"{hours:.1f}-{hours + 0.3:.1f} horas"


def render_incremental_option(parquet_path: Path):
    """
    Renderiza opção de execução incremental na UI.

    Args:
        parquet_path: Caminho do Parquet
    """
    info = get_incremental_info(parquet_path)

    if not info['exists']:
        st.warning("📂 Nenhum arquivo Parquet existente. Execute o pipeline completo primeiro.")
        return

    st.info(f"📊 **Último trimestre processado:** {info['last_quarter']}")

    if info['can_increment']:
        st.success(f"✅ **{info['quarters_behind']} trimestre(s) novo(s) disponível(eis)!**")

        with st.expander("📋 Trimestres a processar"):
            for year, quarter in info['next_quarters']:
                st.write(f"- Q{quarter} {year}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Trimestres novos",
                info['quarters_behind'],
                "prontos para processar"
            )

        with col2:
            estimated_time = estimate_incremental_time(info['quarters_behind'])
            st.metric(
                "Tempo estimado",
                estimated_time,
                "vs 3-4h completo"
            )

        if st.button("▶️ Executar Incremental", key='run_incremental', use_container_width=True):
            st.info("🚧 Pipeline incremental será implementado em breve!")
            # Aqui virá a lógica de execução

    else:
        st.info("✅ Dados já estão atualizados! Nenhum trimestre novo disponível.")


def show_pipeline_comparison():
    """
    Mostra comparação entre pipeline completo vs incremental.
    """
    st.markdown("### 🔄 Comparação dos Modos")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Pipeline Completo**")
        st.markdown("""
        - ✅ Processa tudo do zero
        - ✅ Garante consistência total
        - ⏱️ Demora 3-4 horas
        - 📅 Use para primeira execução
        - 📅 Use se houver problemas nos dados
        """)

    with col2:
        st.markdown("**Pipeline Incremental**")
        st.markdown("""
        - ✅ Processa apenas novos trimestres
        - ✅ Muito mais rápido (~5 min/trimestre)
        - ⏱️ Economiza tempo
        - 📅 Use para atualizações trimestrais
        - 📅 Requer base Parquet existente
        """)

    st.markdown("---")
    st.markdown("💡 **Recomendação:** Use incremental para atualizações regulares e completo apenas quando necessário.")
