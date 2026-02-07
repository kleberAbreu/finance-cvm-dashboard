# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brazilian financial data pipeline that fetches data from **CVM** (Comissão de Valores Mobiliários) and enriches it with market prices from **Yahoo Finance** to generate company valuation reports. Written in Python as a single Jupyter notebook.

**Primary file:** `PipeV5.ipynb` (single-cell notebook)
**Ticker database:** `BASE_EMPRESAS_TICKERS.csv` (CNPJ;Nome;Ticker;Tipo format, semicolon-delimited)
**Output:** `pipeline_cvm_final/outputs/Valuation_Final_YYYYMMDD.xlsx`

## Running

```bash
pip install pandas numpy requests openpyxl tqdm yfinance
jupyter notebook PipeV5.ipynb
```

No build system, tests, or linter configured.

## Configuration

Top of the notebook cell, section "1. CONFIGURAÇÕES":
- `ANO_INICIO` / `ANO_FIM`: year range for data collection (currently 2015–2025)
- `CAMINHO_TICKERS`: path to ticker CSV
- `CVM_BASE_URL`: CVM data source URL

## Architecture (7-Section Pipeline)

All code lives in a single notebook cell with clearly marked sections:

1. **Utilities** (`carregar_tickers_e_tipos`): Reads `BASE_EMPRESAS_TICKERS.csv` with encoding fallbacks. Produces two maps: CNPJ→Ticker and CNPJ→Tipo (sector).

2. **ZIP Reading** (`ler_csv_do_zip`): Generic reader that extracts CSVs from CVM ZIP files by partial name match.

3. **CVM Accounting Engine** (`processar_ano_completo`): Downloads ITR (quarterly) and DFP (annual) ZIPs from CVM. Extracts consolidated statements (DRE, DFC, BPA, BPP). Q1-Q3 from ITR, Q4 calculated as FY12M minus 9M accumulated (both DRE and DFC). Key extractors:
   - `extrair_patrimonio`: Assets, Cash, Equity, Gross/Net Debt
   - `agrupar_contas_resultado`: Hierarchical net income selection (3.11 → 3.11.01 → 3.07 → 3.09) to avoid duplication
   - `agrupar_contas_fluxo`: D&A extraction from cash flow

4. **Market Enrichment** (`enriquecer_com_mercado`): Uses `yfinance` to fetch closing prices and shares outstanding per ticker/quarter. Calculates EBITDA, Market Cap, EV, P/E, EV/EBITDA, P/B, DL/EV.

5. **Summaries** (`gerar_resumos_snapshot`): Snapshot at the latest reporting date. Generates sector-level (grouped by `Tipo`) and market-wide aggregates with median and weighted-average multiples.

6. **Excel Export** (`gerar_excel`): Multi-sheet workbook — Base Consolidada, Resumo_Setores, Resumo_Mercado.

## Key Financial Formulas

- **EBITDA** = Net Income − Financial Results − Taxes + D&A
- **Market Cap** = Price × Shares Outstanding (from Yahoo Finance)
- **EV** = Market Cap + Net Debt
- **P/E** = Market Cap / (4 × Quarterly Net Income)
- **EV/EBITDA** = EV / (4 × Quarterly EBITDA)
- **P/B** = Market Cap / Equity
- **DL/EV** = Net Debt / EV

## Net Income Hierarchy

`agrupar_contas_resultado` uses a fallback chain to avoid double-counting:
1. Account 3.11 (general consolidated)
2. Account 3.11.01 (attributable to controlling shareholders)
3. Account 3.07 (banks)
4. Account 3.09 (fallback)

## Language

All comments, variable names, and UI output are in **Portuguese (Brazilian)**.
