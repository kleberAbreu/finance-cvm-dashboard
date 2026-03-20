# Dashboard de Análise Financeira - CVM

Dashboard interativo em Streamlit para análise e visualização de dados financeiros de empresas brasileiras, combinando dados da **CVM** (Comissão de Valores Mobiliários) com preços de mercado do **Yahoo Finance**.

## 📊 Visão Geral

O dashboard oferece 7 páginas de análise completas:

1. **Overview** - Visão geral do mercado com métricas agregadas
2. **Company Analysis** - Análise individual e comparação de empresas
3. **Sector Comparison** - Benchmarking entre setores
4. **Screener** - Filtro e ranqueamento customizado de empresas
5. **Time Series** - Análise de tendências temporais
6. **Correlations** - Análise de correlações entre métricas
7. **Pipeline Execution** - Execução do pipeline completo ou incremental

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- pip

### Passos de Instalação

```bash
# 1. Clone ou navegue até o diretório do projeto
cd /Users/kleberabreu/Desktop/project-finance-cvm

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute o dashboard
streamlit run app.py
```

O dashboard abrirá automaticamente no navegador em `http://localhost:8501`

## 📂 Estrutura do Projeto

```
project-finance-cvm/
├── app.py                          # Entry point principal
├── requirements.txt                # Dependências Python
├── config/
│   └── settings.py                 # Configurações centralizadas
├── src/
│   ├── data/
│   │   ├── loader.py               # Carregamento e cache de dados
│   │   ├── preprocessor.py         # Transformações e filtros
│   │   └── pipeline_runner.py      # Execução do pipeline (Fase 4)
│   ├── components/
│   │   ├── sidebar.py              # Filtros universais
│   │   ├── metrics_cards.py        # Cards de KPIs
│   │   └── charts.py               # Gráficos Plotly reutilizáveis
│   ├── pages/
│   │   ├── 01_overview.py
│   │   ├── 02_company_analysis.py
│   │   ├── 03_sector_comparison.py
│   │   ├── 04_screener.py
│   │   ├── 05_time_series.py
│   │   └── 06_correlations.py
│   └── utils/
│       ├── formatters.py           # Formatação (BRL, números)
│       ├── calculations.py         # Cálculos financeiros
│       └── validators.py           # Validação de dados
├── BASE_EMPRESAS_TICKERS.csv       # Mapeamento CNPJ→Ticker→Setor
└── pipeline_cvm_final/
    └── outputs/
        └── Valuation_Final_20260207.xlsx  # Dados fonte
```

## 📊 Fonte de Dados

O dashboard utiliza o arquivo Excel gerado pelo pipeline `PipeV5.ipynb`:

- **Arquivo**: `pipeline_cvm_final/outputs/Valuation_Final_20260207.xlsx`
- **3 Planilhas**:
  - `Base Consolidada`: 16.665 registros (210+ empresas × 43 trimestres)
  - `Resumo_Setores`: Agregados por setor
  - `Resumo_Mercado`: Snapshot consolidado

### Métricas Disponíveis

**Balanço Patrimonial:**
- Ativo Total, Caixa, Dívida Bruta/Líquida, Patrimônio Líquido

**Demonstrativo de Resultados:**
- Lucro Líquido, EBITDA, Resultado Financeiro, IR, D&A

**Dados de Mercado:**
- Preço de Fechamento, Quantidade de Ações, Market Cap, Enterprise Value

**Múltiplos de Valuation:**
- P/E, EV/EBITDA, P/B, DL/EV

## 🎯 Funcionalidades Principais

### Filtros Universais (Sidebar)

Aplicados globalmente a todas as páginas:

- **Período**: Date range, trimestres específicos, apenas mais recente
- **Empresas/Setores**: Multi-select com busca
- **Métricas**: Ranges de Market Cap, P/E, EV/EBITDA, P/B
- **Qualidade**: Toggle para remover dados inválidos (NaN/inf)
- **Exportação**: Download CSV/Excel dos dados filtrados

### Página 1: Overview

- Hero metrics (Market Cap Total, # Empresas, múltiplos medianos)
- Composição de mercado (pizza/barras)
- Evolução temporal de métricas agregadas
- Rankings (Top 10 por Market Cap, EBITDA)

### Página 2: Company Analysis

- Perfil detalhado da empresa
- 3 abas de demonstrativos (Balanço, Resultados, Múltiplos)
- Comparação com até 4 peers do mesmo setor
- Benchmarking vs medianas setoriais
- Cálculo de percentil

### Página 3: Sector Comparison

- Comparação de até 10 setores simultaneamente
- Tabela agregada com métricas setoriais
- 4 tipos de visualização: Barras, Bubble chart, Time series, Box plots
- Deep-dive: Top 10 empresas de cada setor

### Página 4: Screener

- Filtros customizados por múltiplas métricas
- Tabela paginada (50 linhas/página)
- Ordenação clicável
- Estatísticas rápidas dos resultados
- Download CSV dos resultados

### Página 5: Time Series

- Visualização de evolução temporal (linha/área/barras)
- Normalização (base 100, % mudança)
- 3 modos: Empresas individuais, Média setorial, Média de mercado
- Cálculo de CAGR e volatilidade
- Range selectors (1A, 3A, 5A, 10A, Tudo)

### Página 6: Correlations

- Scatter plot interativo com regressão linear
- Estatísticas completas (R, R², p-value, slope)
- Matriz de correlação (heatmap)
- Análise separada por setor
- Evolução de correlações ao longo do tempo

### Página 7: Pipeline Execution

- Execução do pipeline CVM completo (3-4h)
- Pipeline incremental (~5 min/trimestre)
- Backup automático antes da execução
- Progress tracking em tempo real
- Log detalhado com timestamps
- Detecção automática de novos trimestres disponíveis

## 🔧 Configurações

Edite `config/settings.py` para personalizar:

```python
# Caminhos
PARQUET_BASE_FILE = DATA_DIR / "base_consolidada.parquet"
TICKERS_FILE = BASE_DIR / "BASE_EMPRESAS_TICKERS.csv"

# Cache
CACHE_TTL = 3600  # 1 hora

# Pipeline
ANO_INICIO_DEFAULT = 2015
ANO_FIM_DEFAULT = 2025
```

## 💡 Uso Rápido

### 1. Análise Rápida das Maiores Empresas

Na sidebar:
1. Ative "Apenas trimestre mais recente"
2. Ajuste "Top N por Market Cap" para 20
3. Navegue pelas páginas para ver análises focadas

### 2. Comparar Bancos vs Varejo

1. Vá para **Sector Comparison**
2. Selecione setores "Bancos" e "Varejo"
3. Compare múltiplos nas abas de visualização

### 3. Encontrar Value Stocks

1. Vá para **Screener**
2. Defina: P/E < 15, P/B < 2
3. Clique "Aplicar"
4. Ordene por Market Cap

### 4. Analisar Tendência de uma Empresa

1. Vá para **Company Analysis**
2. Selecione a empresa
3. Visualize evolução nas 3 abas
4. Compare com peers

## 🐛 Troubleshooting

### Dashboard não carrega

```bash
# Verifique se as dependências estão instaladas
pip list | grep streamlit

# Reinstale se necessário
pip install -r requirements.txt --upgrade
```

### Erro "Arquivo não encontrado"

Verifique se o arquivo Excel existe:
```bash
ls -lh pipeline_cvm_final/outputs/Valuation_Final_20260207.xlsx
```

### Dados não atualizam

Limpe o cache usando o botão "🔄 Limpar Cache" na sidebar

### Performance lenta

- Reduza o período de análise usando filtros de data
- Use "Top N" para limitar empresas
- Ative "Apenas trimestre mais recente"

## 📈 Performance

| Operação | Tempo Esperado |
|----------|----------------|
| Carregamento inicial | < 5s |
| Navegação entre páginas | < 1s |
| Aplicar filtros | < 2s |
| Gerar gráfico | < 3s |
| Export CSV | < 10s |

## 🔮 Próximas Features (Pós-MVP)

- [x] ✅ Execução do pipeline completo via UI (Fase 4 - COMPLETO)
- [x] ✅ Pipeline incremental para atualizações trimestrais (COMPLETO)
- [ ] Scheduler automático para execução periódica
- [ ] Autenticação e perfis de usuário
- [ ] Salvamento de telas/filtros customizados
- [ ] Alertas automáticos por email
- [ ] Geração de relatórios PDF
- [ ] Insights via IA
- [ ] Integração com API do Yahoo Finance (tempo real)

## 📝 Notas Técnicas

### Caching

Utiliza `st.cache_data` com TTL de 1 hora para otimizar performance. Dados são carregados uma vez e reutilizados entre páginas.

### Tipos de Dados Otimizados

Colunas categóricas (Ticker, Setor) usam dtype `category` para reduzir uso de memória (~50% de economia).

### Tratamento de Dados Inválidos

- Valores `inf`/`-inf` substituídos por `NaN`
- Filtro opcional "Apenas dados válidos" na sidebar
- Outliers detectados via método IQR (threshold 1.5)

## 🤝 Contribuindo

Para reportar bugs ou sugerir features:

1. Verifique se o issue já existe
2. Crie um novo issue com descrição detalhada
3. Inclua screenshots se relevante

## 📄 Licença

Projeto interno para análise de dados financeiros CVM.

## 👤 Contato

Para dúvidas sobre uso do dashboard ou dos dados, consulte a documentação em `CLAUDE.md`.

---

**💡 Dica:** Use o atalho `Ctrl+R` (ou `Cmd+R` no Mac) para recarregar o dashboard após mudanças no código.
