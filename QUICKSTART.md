# 🚀 Guia de Início Rápido - Dashboard CVM

## Instalação em 3 Passos

```bash
# 1. Instalar dependências
pip3 install -r requirements.txt

# 2. Executar o dashboard
streamlit run app.py

# 3. Abrir no navegador
# O Streamlit abrirá automaticamente em http://localhost:8501
```

## ✅ Verificação Rápida

Se tudo estiver funcionando, você verá:

1. **Página inicial** com título "Dashboard de Análise Financeira - CVM"
2. **Sidebar à esquerda** com filtros
3. **Informações sobre dados** expansível
4. **Sem erros** no terminal ou navegador

## 🎯 Primeiros Passos

### 1. Explore a Overview (Página inicial)

- Veja métricas agregadas do mercado
- Analise composição por setor
- Observe evolução temporal

### 2. Analise uma Empresa Específica

1. Clique em **"Company Analysis"** na sidebar
2. Selecione uma empresa (ex: PETR4, VALE3)
3. Explore as 3 abas de demonstrativos
4. Compare com peers

### 3. Use o Screener

1. Vá para **"Screener"**
2. Defina critérios de filtro (ex: P/E < 20)
3. Clique "Aplicar"
4. Veja empresas que atendem os critérios

### 4. Compare Setores

1. Vá para **"Sector Comparison"**
2. Selecione 3-5 setores
3. Compare múltiplos nas diferentes visualizações

## 🔧 Troubleshooting Rápido

### Erro: ModuleNotFoundError

```bash
# Reinstalar dependências
pip3 install -r requirements.txt --upgrade
```

### Erro: File not found (Excel)

```bash
# Verificar se o arquivo existe
ls -lh pipeline_cvm_final/outputs/Valuation_Final_20260207.xlsx

# Se não existir, rode o notebook PipeV5.ipynb primeiro
```

### Dashboard muito lento

Na sidebar:
1. Ative "Apenas trimestre mais recente"
2. Use "Top N por Market Cap" = 20
3. Clique "Limpar Cache" se necessário

### Gráficos não aparecem

```bash
# Verificar instalação do Plotly
pip3 show plotly

# Reinstalar se necessário
pip3 install plotly --upgrade
```

## 📊 Dicas de Uso

### Filtros Universais (Sidebar)

Os filtros na sidebar afetam **todas as páginas**:

- **Período**: Ajuste para focar em anos específicos
- **Empresas**: Multi-select para análise focada
- **Setores**: Filtrar por indústria
- **Métricas**: Ranges para screening

### Navegação Eficiente

Use as teclas:

- `Ctrl+R` (Windows/Linux) ou `Cmd+R` (Mac): Recarregar
- Setas ←/→: Navegar entre inputs
- Tab: Pular para próximo campo

### Export de Dados

Em qualquer página:

1. Configure os filtros desejados
2. Clique "Download CSV" na sidebar
3. Dados filtrados serão exportados

## 🎨 Customização

### Alterar Período Padrão

Edite `config/settings.py`:

```python
ANO_INICIO_DEFAULT = 2020  # Em vez de 2015
ANO_FIM_DEFAULT = 2025
```

### Alterar TTL do Cache

Edite `config/settings.py`:

```python
CACHE_TTL = 7200  # 2 horas em vez de 1
```

### Mudar Cores dos Gráficos

Edite `config/settings.py`:

```python
COLOR_PALETTE = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'
]
```

## 📈 Casos de Uso Comuns

### Encontrar Empresas Subavaliadas (Value Investing)

1. **Screener** → Filtros:
   - P/E: 0 - 15
   - P/B: 0 - 2
   - Market Cap: > 1bi
2. Ordenar por P/E
3. Analisar individualmente

### Comparar Performance Setorial

1. **Sector Comparison**
2. Selecionar setores de interesse
3. Aba "Séries Temporais"
4. Métrica: P/E ou EV/EBITDA

### Identificar Tendências de Crescimento

1. **Time Series**
2. Métrica: EBITDA ou Lucro Líquido
3. Normalização: Base 100
4. Selecionar 5-10 empresas
5. Analisar CAGR na seção de tendências

### Descobrir Correlações

1. **Correlations**
2. Eixo X: P/E
3. Eixo Y: EV/EBITDA
4. Analisar R² e significância

## 🆘 Suporte

Para problemas não resolvidos:

1. Verifique `README.md` para documentação completa
2. Consulte `CLAUDE.md` para detalhes técnicos
3. Limpe cache: botão na sidebar
4. Reinicie o Streamlit: `Ctrl+C` e `streamlit run app.py`

## 🎓 Entendendo os Dados

### Métricas Principais

- **P/E**: Preço / Lucro (quanto você paga por cada R$ de lucro)
- **EV/EBITDA**: Enterprise Value / EBITDA (valuation operacional)
- **P/B**: Preço / Patrimônio (quanto vale vs valor contábil)
- **DL/EV**: Dívida Líquida / EV (alavancagem)

### Fonte dos Dados

- **Demonstrativos**: CVM (oficial)
- **Preços**: Yahoo Finance (diário)
- **Período**: Q1 2015 - Q3 2025
- **Empresas**: 210+ listadas

### Frequência de Atualização

Para atualizar dados:

1. Execute o notebook `PipeV5.ipynb` (leva 3+ horas)
2. Novo arquivo Excel será gerado
3. Dashboard carregará automaticamente

---

**Pronto para começar!** 🚀

Execute: `streamlit run app.py`
