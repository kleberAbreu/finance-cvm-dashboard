# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brazilian financial data pipeline that fetches, processes, and consolidates data from **B3** (Brazilian Stock Exchange) and **CVM** (Comissão de Valores Mobiliários) to generate company valuation reports. Written in Python as a single Jupyter notebook.

**Primary file:** `Pegando Cotaçõesv4_202602.ipynb` (single-cell notebook)
**Ticker database:** `BASE_EMPRESAS_TICKERS.csv` (CNPJ;Nome;Ticker;Tipo format, semicolon-delimited)
**Output:** `pipeline_b3_cvm/outputs/Valuation_ZeroYahoo_YYYYMMDD.xlsx`

## Running

```bash
pip install pandas numpy requests openpyxl tqdm
jupyter notebook "Pegando Cotaçõesv4_202602.ipynb"
```

No build system, tests, or linter configured.

## Configuration

Top of the notebook cell, section "⚙️ 1. CONFIGURAÇÕES":
- `ANO_INICIO` / `ANO_FIM`: year range for data collection (currently 2021–2025)
- `CAMINHO_TICKERS`: path to ticker CSV
- `CVM_BASE_URL` / `B3_URL_TEMPLATE`: external data source URLs

## Architecture (5-Stage ETL Pipeline)

All code lives in a single notebook cell with clearly marked sections:

1. **Ticker Loading** (`carregar_tickers`): Reads `BASE_EMPRESAS_TICKERS.csv` with encoding fallbacks. Produces three maps: CNPJ→Ticker, ticker list, CNPJ→Setor.

2. **B3 Price Engine** (`processar_precos_b3`, `download_b3_cotahist`): Downloads COTAHIST ZIP files from B3, parses fixed-width positional format (data pos 2-10, ticker 12-24, price 108-121 with 2 implicit decimals). Processes in 100K-row chunks.

3. **CVM Financial Engine** (`processar_ano_cvm`, `ler_csv_do_zip`): Downloads ITR (quarterly) and DFP (annual) statement ZIPs from CVM. Extracts consolidated statements (DRE, DFC, BPA, BPP). Q4 is calculated as FY12M minus 9M accumulated. Key extractors: `extrair_patrimonio`, `extrair_dre_periodo`, `extrair_dfc_periodo`.

4. **Data Consolidation** (`consolidar_dados`): Joins CVM financials with B3 prices via `pd.merge_asof` (backward, 10-day tolerance). Calculates EBITDA, implicit shares (from LPA), Market Cap, EV, P/E, EV/EBITDA, P/B.

5. **Summary & Export** (`gerar_resumos_snapshot`, `exportar_excel`): Generates sector-level and market-wide aggregate metrics at the latest reporting date. Exports multi-sheet Excel (Dados, Resumo_Setores, Resumo_Mercado).

## Key Financial Formulas

- **EBITDA** = Net Income − Financial Results − Taxes + D&A
- **Implicit Shares** = Net Income / EPS (LPA)
- **Market Cap** = Price × Implicit Shares
- **EV** = Market Cap + Net Debt
- **P/E** = Market Cap / (4 × Quarterly Net Income)
- **EV/EBITDA** = EV / (4 × Quarterly EBITDA)

## Known Issues

- B3 downloads use `verify=False` due to SSL certificate issues
- If B3 download fails, the `consolidar_dados` step crashes with `KeyError: 'DATA'` on an empty DataFrame — no graceful fallback when price data is missing
- Manual fallback: place `COTAHIST_A{YEAR}.ZIP` files in `pipeline_b3_cvm/temp_cache/`

## Language

All comments, variable names, and UI output are in **Portuguese (Brazilian)**.
