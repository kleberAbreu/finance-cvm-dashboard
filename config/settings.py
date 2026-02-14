"""
Configurações centralizadas do dashboard.
"""
from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "pipeline_cvm_final" / "outputs"
TICKERS_FILE = BASE_DIR / "BASE_EMPRESAS_TICKERS.csv"

# Arquivo Excel padrão
DEFAULT_EXCEL = DATA_DIR / "Valuation_Final_20260207.xlsx"

# Nomes das planilhas
SHEET_BASE = "Base Consolidada"
SHEET_SETORES = "Resumo_Setores"
SHEET_MERCADO = "Resumo_Mercado"

# Colunas esperadas (nomes reais do Excel)
COLS_BASE = [
    'CNPJ_CIA', 'DENOM_CIA', 'Ticker', 'Tipo', 'DT_FIM_EXERC',
    'Ativo Total', 'Caixa', 'Divida Bruta', 'Divida Liquida',
    'Patrimonio Liquido', 'Lucro Liquido', 'Res_Fin',
    'IR', 'DA_Trimestral', 'EBITDA', 'Preco_Fechamento', 'Qtd_Acoes_Milhoes',
    'Market_Cap', 'EV', 'P_E', 'EV_EBITDA', 'Price_to_Book', 'DL_EV'
]

# Mapeamento de nomes para padronização (Base Consolidada)
COLUMN_MAPPING = {
    'DENOM_CIA': 'Empresa',
    'DT_FIM_EXERC': 'Data_Trimestre',
    'Divida Bruta': 'Dívida Bruta',
    'Divida Liquida': 'Dívida Líquida',
    'Patrimonio Liquido': 'Patrimônio Líquido',
    'Lucro Liquido': 'Lucro Líquido',
    'Res_Fin': 'Resultado Financeiro',
    'DA_Trimestral': 'D&A',
    'Preco_Fechamento': 'Preço de Fechamento',
    'Qtd_Acoes_Milhoes': 'Qtde Ações',
    'Market_Cap': 'Market Cap',
    'EV': 'Enterprise Value',
    'P_E': 'P/E',
    'EV_EBITDA': 'EV/EBITDA',
    'Price_to_Book': 'P/B',
    'DL_EV': 'DL/EV'
}

# Mapeamento para Resumo_Setores
COLUMN_MAPPING_SETORES = {
    'SETOR': 'Tipo',
    'DT_FIM_EXERC': 'Data_Trimestre',
    'N_Empresas': 'Qtde_Empresas',
    'Market_Cap_Sum': 'Market_Cap_Total',
    'P_E_Median': 'Mediana_PE',
    'EV_EBITDA_Median': 'Mediana_EV_EBITDA',
    'Price_to_Book_Median': 'Mediana_PB'
}

COLS_SETORES = [
    'SETOR', 'DT_FIM_EXERC', 'N_Empresas', 'Market_Cap_Sum',
    'EV_Sum', 'Lucro_Sum', 'EBITDA_Sum', 'Price_to_Book_Median',
    'P_E_Median', 'EV_EBITDA_Median', 'P_E_Agregado', 'EV_EBITDA_Agregado'
]

COLS_MERCADO = [
    'DT_FIM_EXERC', 'N_Empresas', 'Market_Cap_Sum', 'EV_Sum',
    'Lucro_Sum', 'EBITDA_Sum', 'Price_to_Book_Median',
    'P_E_Median', 'EV_EBITDA_Median', 'P_E_Agregado', 'EV_EBITDA_Agregado'
]

# Configurações de visualização
CURRENCY_SCALE = {
    1e12: 'tri',
    1e9: 'bi',
    1e6: 'mi',
    1e3: 'mil'
}

# Configurações de cache
CACHE_TTL = 3600  # 1 hora em segundos

# Configurações do pipeline
ANO_INICIO_DEFAULT = 2015
ANO_FIM_DEFAULT = 2025
CVM_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"

# Temas de cores para gráficos
PLOTLY_TEMPLATE = "plotly_white"
COLOR_PALETTE = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]

# Formatação
LOCALE = 'pt_BR'
DATE_FORMAT = '%Y-%m-%d'
QUARTER_FORMAT = 'Q%q %Y'
