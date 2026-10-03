# Arquitetura

## Visão Geral

O projeto é um dashboard Streamlit multipage com uma camada de dados em Parquet.
O app tenta carregar a base completa gerada pelo pipeline e, se ela não existir,
usa a amostra pública versionada em `data/sample/`.

```text
CVM ZIPs + Yahoo Finance
        ↓
src/data/pipeline_runner.py
        ↓
pipeline_cvm_final/outputs/*.parquet
        ↓
src/data/loader.py
        ↓
src/data/preprocessor.py
        ↓
pages/ + src/components/
```

## Módulos

```text
app.py                  Entrada principal Streamlit
pages/                  Páginas descobertas automaticamente pelo Streamlit
config/settings.py      Caminhos, colunas, cache e constantes
src/components/         Sidebar, cards de métricas e gráficos Plotly
src/data/               Loader, filtros, pipeline completo e incremental
src/utils/              Formatação, validação e cálculos financeiros
data/sample/            Parquets pequenos para demo e testes
tests/                  Testes de comportamento essencial
```

## Dados

Arquivos de produção esperados:

- `pipeline_cvm_final/outputs/base_consolidada.parquet`
- `pipeline_cvm_final/outputs/resumo_setores.parquet`
- `pipeline_cvm_final/outputs/resumo_mercado.parquet`

Arquivos de fallback:

- `data/sample/base_consolidada.parquet`
- `data/sample/resumo_setores.parquet`
- `data/sample/resumo_mercado.parquet`

O fallback é implementado em `src/data/loader.py` por `resolve_data_paths`.

## Pipeline

`PipelineRunner` faz:

1. Download de arquivos ITR/DFP da CVM com retry/backoff.
2. Extração das contas contábeis relevantes.
3. Enriquecimento com preços e ações via Yahoo Finance com retry simples.
4. Cálculo de múltiplos e resumos.
5. Escrita dos Parquets locais.

## Padrões Para Novas Páginas

Crie novas páginas apenas em `pages/`, seguindo o padrão nativo do Streamlit:

```python
import streamlit as st

from config.settings import PARQUET_BASE_FILE
from src.components.sidebar import apply_filters, render_sidebar_filters
from src.data.loader import load_and_prepare_base

st.set_page_config(page_title="Nova Página - Dashboard CVM", layout="wide")

filters = render_sidebar_filters()
df = load_and_prepare_base(PARQUET_BASE_FILE)
df_filtered = apply_filters(df, filters)
```

## Segurança

- O app roda sem login por padrão para facilitar uso local.
- Autenticação só deve ser habilitada em deploy privado via `CVM_DASHBOARD_AUTH=1`
  ou `st.secrets`.
- Segredos e bases completas não devem ser versionados.
