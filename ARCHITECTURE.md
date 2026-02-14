# Arquitetura do Dashboard CVM

## Visão Geral

Dashboard Streamlit multipage para análise financeira de empresas brasileiras. Arquitetura modular com separação clara de responsabilidades.

## Stack Tecnológico

| Componente | Tecnologia | Versão | Uso |
|------------|------------|--------|-----|
| Frontend | Streamlit | 1.32.0 | Interface web interativa |
| Visualizações | Plotly | 5.18.0 | Gráficos interativos |
| Processamento | Pandas | 2.2.0 | Manipulação de dados |
| Cálculos | NumPy | 1.26.3 | Operações numéricas |
| Estatísticas | SciPy | 1.12.0 | Regressão, correlações |
| Excel I/O | openpyxl | 3.1.2 | Leitura/escrita Excel |
| Dados externos | yfinance | 0.2.36 | Preços Yahoo Finance |

## Estrutura de Módulos

```
src/
├── data/              # Camada de dados
│   ├── loader.py      # Carregamento com cache
│   └── preprocessor.py # Transformações e filtros
├── components/        # Componentes reutilizáveis
│   ├── sidebar.py     # Filtros universais
│   ├── metrics_cards.py # KPIs
│   └── charts.py      # Gráficos Plotly
├── pages/             # Páginas do dashboard
│   └── 01_*.py - 06_*.py
└── utils/             # Utilitários
    ├── formatters.py  # Formatação
    ├── calculations.py # Cálculos financeiros
    └── validators.py  # Validações
```

## Fluxo de Dados

```
Excel (CVM + Yahoo) → Loader → Cache → Preprocessor → Filters → Components → UI
                        ↓
                    Validation
```

### 1. Carregamento (loader.py)

```python
@st.cache_data(ttl=3600)
def load_excel_data() -> Tuple[DataFrame, DataFrame, DataFrame]:
    # Lê 3 sheets do Excel
    # Valida estrutura
    # Retorna tupla de DataFrames
```

**Cache**: TTL 1h, evita recarregar a cada interação

### 2. Pré-processamento (preprocessor.py)

- Parsing de datas
- Conversão de tipos (categorical para otimização)
- Limpeza de inf/NaN
- Filtros por data, ticker, setor, métrica

### 3. Filtros Universais (sidebar.py)

```python
filters = render_sidebar_filters()  # UI
df_filtered = apply_filters(df, filters)  # Aplicação
```

**Session State**: Filtros persistem entre páginas

### 4. Componentes (components/)

Funções puras que recebem dados e retornam elementos Streamlit ou Plotly:

```python
render_kpi_card(title, value, delta, format_type)
create_time_series_chart(df, metric, companies)
```

### 5. Páginas (pages/)

Arquitetura de cada página:

```python
# 1. Setup
st.set_page_config(...)

# 2. Carregar dados
df = load_and_prepare_base()

# 3. Aplicar filtros
df_filtered = apply_filters(df, filters)

# 4. Renderizar UI
st.header("...")
render_component(df_filtered)

# 5. Error handling
try:
    ...
except Exception as e:
    st.error(...)
```

## Otimizações de Performance

### 1. Caching Estratificado

| Nível | TTL | Escopo |
|-------|-----|--------|
| Excel load | 1h | Global |
| Aggregations | 1h | Por filtro |
| Charts | N/A | Por renderização |

### 2. Tipos de Dados Otimizados

```python
# Antes: 150 MB em memória
df['Ticker'] = df['Ticker'].astype('object')

# Depois: 75 MB em memória (50% economia)
df['Ticker'] = df['Ticker'].astype('category')
```

Colunas categorizadas:
- Ticker (210 valores únicos)
- Empresa (210 valores)
- Tipo/Setor (48 valores)
- Trimestre (43 valores)

### 3. Lazy Loading

Páginas carregam dados apenas quando acessadas (Streamlit multipage nativo)

### 4. Dataframe Slicing

```python
# Evitar cópias desnecessárias
df_filtered = df[mask]  # Slice eficiente

# Em vez de
df_filtered = df.copy()[mask]  # Cópia + slice
```

## Padrões de Código

### 1. Nomenclatura

- **Funções**: `snake_case` (ex: `load_and_prepare_base`)
- **Classes**: `PascalCase` (atualmente não usado)
- **Constantes**: `UPPER_SNAKE_CASE` (ex: `CACHE_TTL`)
- **Variáveis**: `snake_case` (ex: `df_filtered`)

### 2. Docstrings

Formato Google Style:

```python
def calculate_cagr(start_value: float, end_value: float, periods: int) -> float:
    """
    Calcula Compound Annual Growth Rate (CAGR).

    Args:
        start_value: Valor inicial
        end_value: Valor final
        periods: Número de períodos (anos)

    Returns:
        CAGR como decimal (0.10 = 10%)
    """
```

### 3. Type Hints

Todas as funções principais têm type hints:

```python
from typing import List, Optional, Tuple

def filter_by_tickers(df: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    ...
```

### 4. Error Handling

```python
try:
    # Operação
    result = risky_operation()
except SpecificError as e:
    st.error(f"Erro específico: {str(e)}")
except Exception as e:
    st.error(f"Erro geral: {str(e)}")
    if DEBUG:
        st.exception(traceback.format_exc())
```

## Extensibilidade

### Adicionar Nova Página

1. Criar `src/pages/07_new_page.py`
2. Seguir estrutura padrão:

```python
import streamlit as st
from src.components.sidebar import render_sidebar_filters, apply_filters
from src.data.loader import load_and_prepare_base

st.set_page_config(page_title="New Page", page_icon="🆕", layout="wide")

st.title("🆕 Nova Página")

filters = render_sidebar_filters()
df = load_and_prepare_base()
df_filtered = apply_filters(df, filters)

# Sua lógica aqui
```

3. Streamlit detecta automaticamente

### Adicionar Nova Métrica

1. Certificar que coluna existe no Excel
2. Adicionar em `config/settings.py`:

```python
COLS_BASE = [..., 'Nova_Metrica']
```

3. Usar em qualquer página:

```python
df['Nova_Metrica']  # Acesso direto
```

### Adicionar Novo Gráfico

Em `src/components/charts.py`:

```python
def create_new_chart_type(df: pd.DataFrame, ...) -> go.Figure:
    """
    Descrição do gráfico.
    """
    fig = go.Figure(...)
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig
```

Usar em páginas:

```python
fig = create_new_chart_type(df_filtered, ...)
st.plotly_chart(fig, use_container_width=True)
```

### Adicionar Cálculo Financeiro

Em `src/utils/calculations.py`:

```python
def calculate_new_metric(df: pd.DataFrame, ...) -> pd.Series:
    """
    Descrição do cálculo.
    """
    # Lógica
    return result
```

## Segurança

### 1. Inputs Validados

```python
# Validação de ranges
if min_value > max_value:
    st.error("Valor mínimo maior que máximo")
    st.stop()
```

### 2. SQL Injection N/A

Sem banco de dados, apenas arquivos locais

### 3. XSS Mitigado

Streamlit escapa HTML automaticamente:

```python
st.write(user_input)  # Safe, escaped
st.markdown(user_input, unsafe_allow_html=False)  # Safe
```

### 4. Validação de Dados

`validators.py` verifica:
- Estrutura do Excel
- Colunas esperadas
- Tipos de dados
- Valores duplicados

## Testing Strategy (Futuro)

### Testes Unitários

```python
# tests/test_calculations.py
def test_cagr():
    result = calculate_cagr(100, 121, 2)
    assert result == pytest.approx(0.1, rel=1e-3)
```

### Testes de Integração

```python
# tests/test_pipeline.py
def test_load_and_filter():
    df = load_and_prepare_base(TEST_EXCEL)
    filters = {'tickers': ['PETR4']}
    df_filtered = apply_filters(df, filters)
    assert len(df_filtered) > 0
```

### Testes de UI (Manual)

Checklist em `QUICKSTART.md`

## Monitoramento

### Logs (Futuro)

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Dashboard iniciado")
logger.error(f"Erro ao carregar: {e}")
```

### Métricas (Futuro)

- Tempo de carregamento por página
- Uso de cache (hit rate)
- Erros por tipo
- Páginas mais acessadas

## Deployment (Futuro)

### Opções

1. **Streamlit Cloud**: Deploy gratuito
2. **Heroku**: Container Docker
3. **AWS EC2**: Máquina dedicada
4. **Docker**: `docker-compose up`

### Dockerfile Exemplo

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

## Limitações Atuais

1. **Sem banco de dados**: Dados apenas em Excel
2. **Sem autenticação**: Dashboard público
3. **Sem pipeline UI**: Execução manual do notebook
4. **Cache global**: Não por usuário
5. **Single-threaded**: Streamlit limitation

## Roadmap

### Fase 1 ✅ (Completo)

- [x] Estrutura modular
- [x] 6 páginas funcionais
- [x] Filtros universais
- [x] 20+ tipos de gráficos
- [x] Exportação CSV

### Fase 2 (Em desenvolvimento)

- [ ] Testes automatizados
- [ ] CI/CD pipeline
- [ ] Logs estruturados

### Fase 3 (Futuro)

- [ ] Autenticação
- [ ] Banco de dados
- [ ] API REST
- [ ] Cache por usuário

### Fase 4 (Pipeline Integration)

- [ ] Execução pipeline via UI
- [ ] Progress tracking
- [ ] Scheduler automático

## Contribuindo

Ver `CONTRIBUTING.md` (a ser criado)

## Licença

Projeto interno - uso restrito
