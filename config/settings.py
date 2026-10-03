"""
Configurações centralizadas do dashboard.
"""
import os
from datetime import datetime
from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "pipeline_cvm_final" / "outputs"
SAMPLE_DATA_DIR = BASE_DIR / "data" / "sample"
TICKERS_FILE = BASE_DIR / "BASE_EMPRESAS_TICKERS.csv"

# Arquivos Parquet padrão
PARQUET_BASE_FILE = DATA_DIR / "base_consolidada.parquet"
PARQUET_SETORES_FILE = DATA_DIR / "resumo_setores.parquet"
PARQUET_MERCADO_FILE = DATA_DIR / "resumo_mercado.parquet"

# Arquivos Parquet de amostra versionados para uso local imediato
SAMPLE_PARQUET_BASE_FILE = SAMPLE_DATA_DIR / "base_consolidada.parquet"
SAMPLE_PARQUET_SETORES_FILE = SAMPLE_DATA_DIR / "resumo_setores.parquet"
SAMPLE_PARQUET_MERCADO_FILE = SAMPLE_DATA_DIR / "resumo_mercado.parquet"

# Nomes para referência interna (legado/tabelas)
SHEET_BASE = "Base Consolidada"
SHEET_SETORES = "Resumo_Setores"
SHEET_MERCADO = "Resumo_Mercado"

# Colunas esperadas (nomes reais do parquet)
COLS_BASE = [
    'CNPJ_CIA', 'DENOM_CIA', 'Ticker', 'Tipo', 'DT_FIM_EXERC',
    # Ativo
    'Ativo Total', 'Ativo Circulante', 'Caixa', 'Aplicacoes Financeiras',
    'Contas a Receber', 'Estoques', 'Ativo Nao Circulante',
    'Imobilizado', 'Intangivel',
    # Passivo
    'Passivo Circulante', 'Passivo Nao Circulante',
    'Divida Bruta', 'Divida Liquida', 'Patrimonio Liquido',
    # DRE
    'Receita_Liquida', 'CPV', 'Lucro_Bruto', 'Despesas_Operacionais',
    'EBIT', 'Lucro Liquido', 'Res_Fin', 'IR', 'DA_Trimestral', 'EBITDA',
    # DFC
    'FCO', 'FCI', 'FCF',
    'Caixa_Gerado_Ops', 'Var_Ativos_Passivos', 'Outros_Operacional',
    'Var_Cambial', 'Var_Liquida_Caixa', 'Saldo_Inicial_Caixa',
    'Saldo_Final_Caixa',
    # Mercado
    'Preco_Fechamento', 'Qtd_Acoes_Milhoes',
    'Market_Cap', 'EV', 'P_E', 'EV_EBITDA', 'Price_to_Book', 'DL_EV'
]

# Mapeamento de nomes para padronização (Base Consolidada)
COLUMN_MAPPING = {
    'DENOM_CIA': 'Empresa',
    'DT_FIM_EXERC': 'Data_Trimestre',
    # Ativo
    'Ativo Circulante': 'Ativo Circulante',
    'Aplicacoes Financeiras': 'Aplicações Financeiras',
    'Contas a Receber': 'Contas a Receber',
    'Estoques': 'Estoques',
    'Ativo Nao Circulante': 'Ativo Não Circulante',
    'Imobilizado': 'Imobilizado',
    'Intangivel': 'Intangível',
    # Passivo
    'Passivo Total': 'Passivo Total',
    'Passivo Circulante': 'Passivo Circulante',
    'Passivo Nao Circulante': 'Passivo Não Circulante',
    'Divida Bruta': 'Dívida Bruta',
    'Divida Liquida': 'Dívida Líquida',
    'Patrimonio Liquido': 'Patrimônio Líquido',
    # DRE
    'Receita_Liquida': 'Receita Líquida',
    'CPV': 'CPV',
    'Lucro_Bruto': 'Lucro Bruto',
    'Despesas_Operacionais': 'Despesas Operacionais',
    'EBIT': 'EBIT',
    'Lucro Liquido': 'Lucro Líquido',
    'Res_Fin': 'Resultado Financeiro',
    'DA_Trimestral': 'D&A',
    # DFC
    'FCO': 'FCO',
    'FCI': 'FCI',
    'FCF': 'FCF',
    'Caixa_Gerado_Ops': 'Caixa Gerado nas Operações',
    'Var_Ativos_Passivos': 'Variações Ativos e Passivos',
    'Outros_Operacional': 'Outros (Operacional)',
    'Var_Cambial': 'Variação Cambial',
    'Var_Liquida_Caixa': 'Variação Líquida de Caixa',
    'Saldo_Inicial_Caixa': 'Saldo Inicial de Caixa',
    'Saldo_Final_Caixa': 'Saldo Final de Caixa',
    # Mercado
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
ANO_INICIO_DEFAULT = int(os.getenv("CVM_ANO_INICIO", "2015"))
ANO_FIM_DEFAULT = int(os.getenv("CVM_ANO_FIM", str(datetime.now().year)))
CVM_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"

# Temas de cores para gráficos
PLOTLY_TEMPLATE = "plotly_white"
COLOR_PALETTE = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
]

# Formatação
LOCALE = 'pt_BR'
DATE_FORMAT = '%Y-%m-%d'
QUARTER_FORMAT = 'Q%q %Y'
