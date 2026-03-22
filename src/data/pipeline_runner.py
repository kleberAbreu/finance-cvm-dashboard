"""
Pipeline Runner - Execução do processamento CVM + Yahoo Finance
Extraído de PipeV5.ipynb com adições de progress tracking
"""
import pandas as pd
import numpy as np
import requests
import zipfile
import os
import re
import sys
import logging
import warnings
import contextlib
import yfinance as yf
from datetime import datetime, timedelta
from tqdm import tqdm
from pathlib import Path
from typing import Callable, Optional, Tuple


class PipelineRunner:
    """
    Classe principal para execução do pipeline CVM.
    Suporta modo completo e incremental.
    """

    def __init__(self, ano_inicio: int = 2015, ano_fim: int = 2025,
                 progress_callback: Optional[Callable] = None):
        """
        Inicializa o pipeline runner.

        Args:
            ano_inicio: Ano inicial para processamento
            ano_fim: Ano final para processamento
            progress_callback: Função callback(progress_pct, message)
        """
        self.ano_inicio = ano_inicio
        self.ano_fim = ano_fim
        self.progress_callback = progress_callback

        # Diretórios
        self.base_dir = Path("pipeline_cvm_final")
        self.raw_dir = self.base_dir / "temp_cache"
        self.output_dir = self.base_dir / "outputs"

        # Configurações
        self.caminho_tickers = "BASE_EMPRESAS_TICKERS.csv"
        self.cvm_base_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/"

        # Estado
        self.total_steps = 0
        self.current_step = 0

    def _update_progress(self, message: str, step_increment: int = 1):
        """Atualiza progresso se callback disponível."""
        self.current_step += step_increment
        if self.progress_callback and self.total_steps > 0:
            pct = min(self.current_step / self.total_steps, 1.0)
            self.progress_callback(pct, message)

    # ==========================================================================
    # FUNÇÕES UTILITÁRIAS
    # ==========================================================================

    def setup_directories(self):
        """Cria diretórios necessários."""
        for path in [self.raw_dir, self.output_dir]:
            path.mkdir(parents=True, exist_ok=True)
        self._update_progress("📂 Diretórios configurados")

    @staticmethod
    def limpar_cnpj(cnpj):
        """Remove caracteres não numéricos do CNPJ."""
        return re.sub(r'\D', '', str(cnpj))

    @staticmethod
    def converter_escala(valor, escala):
        """Converte valor conforme escala (MIL/MILHAR ou UNIDADE)."""
        if pd.isna(valor):
            return 0.0
        if escala in ('MIL', 'MILHAR'):
            return valor * 1000.0
        return valor

    @staticmethod
    @contextlib.contextmanager
    def suppress_output():
        """Context manager para suprimir output."""
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = devnull
                sys.stderr = devnull
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    def download_zip_temporario(self, tipo: str, ano: int) -> Optional[Path]:
        """
        Baixa arquivo ZIP da CVM (ITR ou DFP).

        Args:
            tipo: 'ITR' ou 'DFP'
            ano: Ano do arquivo

        Returns:
            Path do arquivo baixado ou None se erro
        """
        filename = f"{tipo.lower()}_cia_aberta_{ano}.zip"
        url = f"{self.cvm_base_url}{tipo}/DADOS/{filename}"
        file_path = self.raw_dir / filename

        if file_path.exists():
            self._update_progress(f"✓ {filename} (cache)", 0)
            return file_path

        try:
            r = requests.get(url, stream=True, timeout=30)
            if r.status_code == 200:
                total_size = int(r.headers.get('content-length', 0))

                with open(file_path, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Update a cada 10%
                        if total_size > 0 and downloaded % (total_size // 10) < 8192:
                            pct = downloaded / total_size
                            self._update_progress(f"⬇️ {filename} ({pct:.0%})", 0)

                self._update_progress(f"✓ {filename} baixado")
                return file_path
            else:
                self._update_progress(f"❌ {filename} não disponível ({r.status_code})", 0)
                return None

        except Exception as e:
            self._update_progress(f"❌ Erro {filename}: {str(e)[:50]}", 0)
            return None

    def limpar_cache_ano(self, ano: int):
        """Remove arquivos ZIP de um ano específico."""
        for f in self.raw_dir.glob(f"*{ano}*.zip"):
            try:
                f.unlink()
            except:
                pass

    def carregar_tickers_e_tipos(self) -> Tuple[dict, dict]:
        """
        Carrega mapeamento CNPJ -> Ticker e CNPJ -> Tipo.

        Returns:
            Tuple (dict_tickers, dict_tipos)
        """
        self._update_progress("📖 Carregando mapeamento de tickers...")

        caminho = Path(self.caminho_tickers)
        if not caminho.exists():
            self._update_progress("⚠️ Arquivo de tickers não encontrado", 0)
            return {}, {}

        encodings = ['utf-8-sig', 'latin1', 'cp1252']
        for enc in encodings:
            try:
                df = pd.read_csv(caminho, sep=';', dtype=str, encoding=enc)
                df.columns = df.columns.str.upper().str.strip()

                if 'CNPJ' in df.columns and 'TICKER' in df.columns:
                    df['CNPJ_CLEAN'] = df['CNPJ'].apply(self.limpar_cnpj)
                    df['TICKER'] = df['TICKER'].str.strip().str.upper()

                    if 'TIPO' not in df.columns:
                        df['TIPO'] = 'N/A'
                    else:
                        df['TIPO'] = df['TIPO'].str.strip()

                    map_tickers = dict(zip(df['CNPJ_CLEAN'], df['TICKER']))
                    map_tipos = dict(zip(df['CNPJ_CLEAN'], df['TIPO']))

                    self._update_progress(f"✓ {len(map_tickers)} tickers carregados")
                    return map_tickers, map_tipos

            except Exception as e:
                continue

        self._update_progress("❌ Erro ao ler arquivo de tickers", 0)
        return {}, {}

    # ==========================================================================
    # LEITURA DE ARQUIVOS ZIP
    # ==========================================================================

    def ler_csv_do_zip(self, path_zip: Optional[Path], nome_csv_parcial: str,
                       colunas: list) -> pd.DataFrame:
        """
        Lê CSV de dentro de um arquivo ZIP.

        Args:
            path_zip: Caminho do arquivo ZIP
            nome_csv_parcial: Parte do nome do CSV a procurar
            colunas: Lista de colunas desejadas

        Returns:
            DataFrame com dados
        """
        if not path_zip or not path_zip.exists():
            return pd.DataFrame()

        try:
            with zipfile.ZipFile(path_zip, 'r') as z:
                arquivos = z.namelist()
                arquivo = next(
                    (f for f in arquivos
                     if nome_csv_parcial.lower() in f.lower() and f.endswith('.csv')),
                    None
                )

                if not arquivo:
                    return pd.DataFrame()

                # Ler header para verificar colunas
                with z.open(arquivo) as f:
                    header = pd.read_csv(f, sep=';', encoding='latin1', nrows=0)
                    cols_disponiveis = [c for c in colunas if c in header.columns]

                # Ler dados
                with z.open(arquivo) as f:
                    df = pd.read_csv(f, sep=';', encoding='latin1',
                                   usecols=cols_disponiveis, low_memory=False)

            # Filtrar apenas ÚLTIMO exercício
            if 'ORDEM_EXERC' in df.columns:
                df = df[df['ORDEM_EXERC'] == 'ÚLTIMO']

            # Converter datas
            if 'DT_FIM_EXERC' in df.columns:
                df['DT_FIM_EXERC'] = pd.to_datetime(df['DT_FIM_EXERC'])
            if 'DT_INI_EXERC' in df.columns:
                df['DT_INI_EXERC'] = pd.to_datetime(df['DT_INI_EXERC'])

            # Converter escala
            if 'VL_CONTA' in df.columns and 'ESCALA_MOEDA' in df.columns:
                df['VL_REAL'] = df.apply(
                    lambda x: self.converter_escala(x['VL_CONTA'], x['ESCALA_MOEDA']),
                    axis=1
                )

            # Limpar CNPJ
            if 'CNPJ_CIA' in df.columns:
                df['CNPJ_CLEAN'] = df['CNPJ_CIA'].apply(self.limpar_cnpj)

            return df

        except Exception as e:
            return pd.DataFrame()

    # ==========================================================================
    # ENGINE DE PROCESSAMENTO CONTÁBIL
    # ==========================================================================

    def ler_csv_con_com_fallback(self, path_zip: Optional[Path], nome_base: str,
                                 colunas: list) -> pd.DataFrame:
        """
        Fix Bug 3: tenta ler versão consolidada (_con) do CSV.
        Se vazia, faz fallback para versão individual (_ind).
        Exemplo: nome_base='DRE' → tenta 'DRE_con', depois 'DRE_ind'
        """
        df_con = self.ler_csv_do_zip(path_zip, f"{nome_base}_con", colunas)
        if not df_con.empty:
            return df_con
        df_ind = self.ler_csv_do_zip(path_zip, f"{nome_base}_ind", colunas)
        if not df_ind.empty:
            self._update_progress(f"  ℹ️ {nome_base}: usando versão individual (_ind) como fallback", 0)
        return df_ind

    def extrair_patrimonio(self, df_bpa: pd.DataFrame, df_bpp: pd.DataFrame,
                          data: pd.Timestamp) -> pd.DataFrame:
        """Extrai dados patrimoniais de uma data específica."""
        bpa_d = df_bpa[df_bpa['DT_FIM_EXERC'] == data]
        bpp_d = df_bpp[df_bpp['DT_FIM_EXERC'] == data]

        if bpa_d.empty or bpp_d.empty:
            return pd.DataFrame()

        # ---- ATIVO (BPA) ----
        ativo_total       = bpa_d[bpa_d['CD_CONTA'] == '1'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        ativo_circ        = bpa_d[bpa_d['CD_CONTA'] == '1.01'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        caixa             = bpa_d[bpa_d['CD_CONTA'] == '1.01.01'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        aplicacoes        = bpa_d[bpa_d['CD_CONTA'] == '1.01.02'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        contas_a_receber  = bpa_d[bpa_d['CD_CONTA'] == '1.01.03'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        estoques          = bpa_d[bpa_d['CD_CONTA'] == '1.01.04'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        ativo_nao_circ    = bpa_d[bpa_d['CD_CONTA'] == '1.02'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        imobilizado       = bpa_d[bpa_d['CD_CONTA'] == '1.02.03'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        intangivel        = bpa_d[bpa_d['CD_CONTA'] == '1.02.04'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()

        # ---- PASSIVO (BPP) ----
        passivo_total     = bpp_d[bpp_d['CD_CONTA'] == '2'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        passivo_circ      = bpp_d[bpp_d['CD_CONTA'] == '2.01'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        passivo_nao_circ  = bpp_d[bpp_d['CD_CONTA'] == '2.02'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()

        # PL: empresas normais usam 2.03, bancos COSIF usam 2.07 ou 2.08
        # Buscar conta top-level (2.XX) cuja descrição contenha "Patrimônio Líquido"
        if 'DS_CONTA' in bpp_d.columns:
            mask_pl = (
                bpp_d['CD_CONTA'].str.match(r'^2\.\d{2}$') &
                bpp_d['DS_CONTA'].str.contains('Patrimônio Líquido', case=False, na=False)
            )
            if mask_pl.any():
                pl = bpp_d[mask_pl].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
            else:
                pl = bpp_d[bpp_d['CD_CONTA'] == '2.03'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()
        else:
            pl = bpp_d[bpp_d['CD_CONTA'] == '2.03'].groupby('CNPJ_CLEAN')['VL_REAL'].sum()

        divida            = bpp_d[bpp_d['CD_CONTA'].isin(['2.01.04', '2.02.01'])].groupby('CNPJ_CLEAN')['VL_REAL'].sum()

        res = pd.DataFrame({
            'Ativo Total':              ativo_total,
            'Ativo Circulante':         ativo_circ,
            'Caixa':                    caixa,
            'Aplicacoes Financeiras':   aplicacoes,
            'Contas a Receber':         contas_a_receber,
            'Estoques':                 estoques,
            'Ativo Nao Circulante':     ativo_nao_circ,
            'Imobilizado':              imobilizado,
            'Intangivel':               intangivel,
            'Passivo Total':            passivo_total,
            'Passivo Circulante':       passivo_circ,
            'Passivo Nao Circulante':   passivo_nao_circ,
            'Patrimonio Liquido':       pl,
            'Divida Bruta':             divida,
        }).reset_index()

        res['Divida Liquida'] = res['Divida Bruta'].fillna(0) - res['Caixa'].fillna(0)
        return res

    def agrupar_contas_resultado(self, df_conta: pd.DataFrame, col_valor: str) -> pd.DataFrame:
        """
        Extrai contas do DRE completo:
          3.01 → Receita Líquida
          3.02 → CPV / CMV
          3.03 → Lucro Bruto
          3.04 → Despesas Operacionais
          3.05 → EBIT (Resultado antes do Financeiro)
          3.06 → Resultado Financeiro
          3.08 → IR / CSLL
          3.11 (ou 3.07/3.09) → Lucro Líquido (hierarquia)
        """
        resultados = []

        for cnpj, grupo in df_conta.groupby('CNPJ_CLEAN'):
            # --- Contas DRE granulares ---
            receita_liquida = grupo[grupo['CD_CONTA'] == '3.01'][col_valor].sum()
            cpv = grupo[grupo['CD_CONTA'] == '3.02'][col_valor].sum()
            lucro_bruto = grupo[grupo['CD_CONTA'] == '3.03'][col_valor].sum()
            despesas_op = grupo[grupo['CD_CONTA'] == '3.04'][col_valor].sum()
            ebit = grupo[grupo['CD_CONTA'] == '3.05'][col_valor].sum()

            # --- Lucro Líquido com hierarquia ---
            ll = 0
            val_311 = grupo[grupo['CD_CONTA'] == '3.11'][col_valor].sum()
            if val_311 != 0:
                ll = val_311
            else:
                val_31101 = grupo[grupo['CD_CONTA'] == '3.11.01'][col_valor].sum()
                if val_31101 != 0:
                    ll = val_31101
                else:
                    val_307 = grupo[grupo['CD_CONTA'] == '3.07'][col_valor].sum()
                    if val_307 != 0:
                        ll = val_307
                    else:
                        ll = grupo[grupo['CD_CONTA'] == '3.09'][col_valor].sum()

            rf = grupo[grupo['CD_CONTA'] == '3.06'][col_valor].sum()
            ir = grupo[grupo['CD_CONTA'] == '3.08'][col_valor].sum()

            resultados.append({
                'CNPJ_CLEAN': cnpj,
                'Receita_Liquida': receita_liquida,
                'CPV': cpv,
                'Lucro_Bruto': lucro_bruto,
                'Despesas_Operacionais': despesas_op,
                'EBIT': ebit,
                'Lucro Liquido': ll,
                'Res_Fin': rf,
                'IR': ir
            })

        return pd.DataFrame(resultados)

    def extrair_dre_trimestral(self, df_dre_trim: pd.DataFrame,
                              data: pd.Timestamp) -> pd.DataFrame:
        """Extrai DRE de um trimestre específico."""
        d = df_dre_trim[df_dre_trim['DT_FIM_EXERC'] == data]
        res = self.agrupar_contas_resultado(d, 'VL_REAL')

        if not d.empty and 'DT_INI_EXERC' in d.columns:
            dt_ini = d[['CNPJ_CLEAN', 'DT_INI_EXERC']].drop_duplicates().set_index('CNPJ_CLEAN')
            res = res.merge(dt_ini, left_on='CNPJ_CLEAN', right_index=True, how='left')
            res.rename(columns={'DT_INI_EXERC': 'DT_INI_REAL'}, inplace=True)

        return res

    def agrupar_contas_fluxo(self, df_conta: pd.DataFrame, col_valor: str) -> pd.DataFrame:
        """Extrai FCO, FCI, FCF, sub-contas e D&A do fluxo de caixa."""
        # Totais principais
        fco = df_conta[df_conta['CD_CONTA'] == '6.01'].groupby('CNPJ_CLEAN')[col_valor].sum()
        fci = df_conta[df_conta['CD_CONTA'] == '6.02'].groupby('CNPJ_CLEAN')[col_valor].sum()
        fcf = df_conta[df_conta['CD_CONTA'] == '6.03'].groupby('CNPJ_CLEAN')[col_valor].sum()

        # Sub-contas operacionais (6.01.xx)
        caixa_gerado_ops   = df_conta[df_conta['CD_CONTA'] == '6.01.01'].groupby('CNPJ_CLEAN')[col_valor].sum()
        var_ativos_passivos = df_conta[df_conta['CD_CONTA'] == '6.01.02'].groupby('CNPJ_CLEAN')[col_valor].sum()
        outros_operacional  = df_conta[df_conta['CD_CONTA'] == '6.01.03'].groupby('CNPJ_CLEAN')[col_valor].sum()

        # Variação cambial e saldo de caixa
        var_cambial        = df_conta[df_conta['CD_CONTA'] == '6.04'].groupby('CNPJ_CLEAN')[col_valor].sum()
        var_liquida_caixa  = df_conta[df_conta['CD_CONTA'] == '6.05'].groupby('CNPJ_CLEAN')[col_valor].sum()
        saldo_inicial      = df_conta[df_conta['CD_CONTA'] == '6.05.01'].groupby('CNPJ_CLEAN')[col_valor].sum()
        saldo_final        = df_conta[df_conta['CD_CONTA'] == '6.05.02'].groupby('CNPJ_CLEAN')[col_valor].sum()

        # DA: 6.01.01 com descrição deprecia/amortiza
        if 'DS_CONTA' in df_conta.columns:
            df_conta = df_conta.copy()
            df_conta['DS_LOWER'] = df_conta['DS_CONTA'].astype(str).str.lower()
            mask = (df_conta['CD_CONTA'].str.startswith('6.01.01')) & \
                   (df_conta['DS_LOWER'].str.contains('deprecia') |
                    df_conta['DS_LOWER'].str.contains('amortiza'))
        else:
            mask = df_conta['CD_CONTA'].str.startswith('6.01.01')

        da = df_conta[mask].groupby('CNPJ_CLEAN')[col_valor].sum()

        res = pd.DataFrame({
            'FCO': fco, 'FCI': fci, 'FCF': fcf, 'DA_Trimestral': da,
            'Caixa_Gerado_Ops': caixa_gerado_ops,
            'Var_Ativos_Passivos': var_ativos_passivos,
            'Outros_Operacional': outros_operacional,
            'Var_Cambial': var_cambial,
            'Var_Liquida_Caixa': var_liquida_caixa,
            'Saldo_Inicial_Caixa': saldo_inicial,
            'Saldo_Final_Caixa': saldo_final,
        }).reset_index()
        return res

    def extrair_dfc_trimestral(self, df_dfc: pd.DataFrame,
                              data: pd.Timestamp) -> pd.DataFrame:
        """Extrai DFC de um trimestre específico."""
        d = df_dfc[df_dfc['DT_FIM_EXERC'] == data].copy()
        if d.empty:
            return pd.DataFrame(columns=['CNPJ_CLEAN', 'FCO', 'FCI', 'FCF', 'DA_Trimestral',
                                          'Caixa_Gerado_Ops', 'Var_Ativos_Passivos', 'Outros_Operacional',
                                          'Var_Cambial', 'Var_Liquida_Caixa', 'Saldo_Inicial_Caixa', 'Saldo_Final_Caixa'])
        return self.agrupar_contas_fluxo(d, 'VL_REAL')

    def processar_ano_completo(self, ano: int) -> pd.DataFrame:
        """
        Processa um ano completo (ITR + DFP).

        Args:
            ano: Ano a processar

        Returns:
            DataFrame com dados do ano
        """
        self._update_progress(f"⚙️ Processando ano {ano}...")

        # Download arquivos
        path_itr = self.download_zip_temporario('ITR', ano)
        path_dfp = self.download_zip_temporario('DFP', ano)

        # Colunas necessárias
        cols_base = ['CNPJ_CIA', 'DENOM_CIA', 'DT_FIM_EXERC', 'CD_CONTA',
                    'DS_CONTA', 'VL_CONTA', 'ESCALA_MOEDA', 'ORDEM_EXERC']
        cols_fluxo = cols_base + ['DT_INI_EXERC']

        # Ler arquivos ITR (con com fallback para ind)
        self._update_progress(f"📖 Lendo ITR {ano}...", 0)
        itr_dre = self.ler_csv_con_com_fallback(path_itr, 'DRE', cols_fluxo)
        itr_dfc = self.ler_csv_con_com_fallback(path_itr, 'DFC_MI', cols_fluxo)
        itr_bpa = self.ler_csv_con_com_fallback(path_itr, 'BPA', cols_base)
        itr_bpp = self.ler_csv_con_com_fallback(path_itr, 'BPP', cols_base)

        if itr_dre.empty:
            self._update_progress(f"⚠️ Sem dados ITR para {ano}")
            return pd.DataFrame()

        # Filtrar trimestres (Q1, Q2, Q3)
        itr_dre['DIAS'] = (itr_dre['DT_FIM_EXERC'] - itr_dre['DT_INI_EXERC']).dt.days
        mask_trim = (itr_dre['DIAS'] >= 80) & (itr_dre['DIAS'] <= 100)
        dre_q123 = itr_dre[mask_trim].copy()

        # Preparar dados 9M para cálculo Q4
        # Fix Bug 2: filtrar também por ano para evitar contaminação entre exercícios
        mask_9m = (
            (itr_dre['DT_INI_EXERC'].dt.month == 1) &
            (itr_dre['DT_FIM_EXERC'].dt.month == 9) &
            (itr_dre['DT_FIM_EXERC'].dt.year == ano)
        )
        dre_9m = itr_dre[mask_9m][['CNPJ_CLEAN', 'CD_CONTA', 'VL_REAL']].rename(columns={'VL_REAL': 'VL_9M'})

        dfc_9m = pd.DataFrame()
        if not itr_dfc.empty:
            mask_9m_dfc = (
                (itr_dfc['DT_INI_EXERC'].dt.month == 1) &
                (itr_dfc['DT_FIM_EXERC'].dt.month == 9) &
                (itr_dfc['DT_FIM_EXERC'].dt.year == ano)
            )
            dfc_9m = itr_dfc[mask_9m_dfc][['CNPJ_CLEAN', 'CD_CONTA', 'VL_REAL']].rename(columns={'VL_REAL': 'VL_9M'})

        # Ler arquivos DFP (con com fallback para ind)
        self._update_progress(f"📖 Lendo DFP {ano}...", 0)
        dfp_dre = self.ler_csv_con_com_fallback(path_dfp, 'DRE', cols_fluxo)
        dfp_dfc = self.ler_csv_con_com_fallback(path_dfp, 'DFC_MI', cols_fluxo)
        dfp_bpa = self.ler_csv_con_com_fallback(path_dfp, 'BPA', cols_base)
        dfp_bpp = self.ler_csv_con_com_fallback(path_dfp, 'BPP', cols_base)

        # Processar trimestres Q1, Q2, Q3
        resultados = []
        datas_itr = sorted(pd.to_datetime(itr_bpa['DT_FIM_EXERC'].unique()))

        for idx, data in enumerate(datas_itr):
            if data.month == 12:
                continue

            self._update_progress(f"  Q{data.quarter} {ano}...", 0)

            patrimonio = self.extrair_patrimonio(itr_bpa, itr_bpp, data)
            if patrimonio.empty:
                continue

            dre_data = self.extrair_dre_trimestral(dre_q123, data)
            dfc_val = self.extrair_dfc_trimestral(itr_dfc, data)

            trimestre = patrimonio.merge(dre_data, on='CNPJ_CLEAN', how='left') \
                                  .merge(dfc_val, on='CNPJ_CLEAN', how='left')

            trimestre['DT_FIM_EXERC'] = data
            trimestre['DT_INI_TRIM'] = data - timedelta(days=90)

            if not dre_data.empty and 'DT_INI_REAL' in dre_data.columns:
                trimestre['DT_INI_TRIM'] = dre_data['DT_INI_REAL']

            resultados.append(trimestre)

        # Processar Q4 (12M - 9M)
        if not dfp_dre.empty:
            self._update_progress(f"  Q4 {ano} (calculado)...", 0)

            dt_q4 = pd.Timestamp(f"{ano}-12-31")
            dt_ini_q4 = pd.Timestamp(f"{ano}-10-01")

            patrimonio_q4 = self.extrair_patrimonio(dfp_bpa, dfp_bpp, dt_q4)

            # DRE anual
            dfp_anual = dfp_dre[dfp_dre['DT_INI_EXERC'].dt.month == 1][['CNPJ_CLEAN', 'CD_CONTA', 'VL_REAL']]

            # Calcular Q4 = 12M - 9M
            # Fix Bug 1: NÃO fazer fillna(0) no VL_9M.
            # Se empresa não tem 9M no ITR (ex: bancos que só entregam individual),
            # VL_9M fica NaN → VL_Q4 fica NaN → dado ausente em vez de dado errado.
            dre_calc = dfp_anual.merge(dre_9m, on=['CNPJ_CLEAN', 'CD_CONTA'], how='left')
            # Identificar CNPJs que NÃO têm nenhum dado 9M — para esses, Q4 = NaN
            cnpjs_sem_9m = set(dfp_anual['CNPJ_CLEAN'].unique()) - set(dre_9m['CNPJ_CLEAN'].unique())
            dre_calc['VL_Q4'] = dre_calc['VL_REAL'] - dre_calc['VL_9M']
            # Para CNPJs sem 9M: forçar todas as contas DRE para NaN
            if cnpjs_sem_9m:
                mask_sem_9m = dre_calc['CNPJ_CLEAN'].isin(cnpjs_sem_9m)
                dre_calc.loc[mask_sem_9m, 'VL_Q4'] = float('nan')
                self._update_progress(
                    f"  ⚠️ Q4 {ano}: {len(cnpjs_sem_9m)} empresas sem ITR 9M → DRE Q4 = NaN", 0
                )

            # Bug A+B: verificar inconsistência de escala (9M > anual em mais de 10%)
            # Comparar APENAS pela conta de receita (3.01) para evitar falsos positivos
            # causados pela soma de contas positivas + negativas no DRE
            _receita_only = dre_calc[dre_calc['CD_CONTA'] == '3.01'][['CNPJ_CLEAN', 'VL_REAL', 'VL_9M']].copy()
            _scale_bad = _receita_only[
                _receita_only['VL_9M'].notna() &
                _receita_only['VL_REAL'].notna() &
                (_receita_only['VL_REAL'].abs() > 0) &
                (_receita_only['VL_9M'].abs() > _receita_only['VL_REAL'].abs() * 1.1)
            ]['CNPJ_CLEAN'].tolist()
            if _scale_bad:
                dre_calc.loc[dre_calc['CNPJ_CLEAN'].isin(_scale_bad), 'VL_Q4'] = float('nan')
                self._update_progress(
                    f"  ⚠️ Q4 {ano}: {len(_scale_bad)} CNPJs com inconsistência de escala → VL_Q4 = NaN", 0
                )

            dre_q4_final = self.agrupar_contas_resultado(dre_calc, 'VL_Q4')

            # DFC Q4
            dfc_q4_final = pd.DataFrame(columns=['CNPJ_CLEAN', 'FCO', 'FCI', 'FCF', 'DA_Trimestral'])
            if not dfp_dfc.empty and not dfc_9m.empty:
                dfp_dfc_anual = dfp_dfc[dfp_dfc['DT_INI_EXERC'].dt.month == 1][['CNPJ_CLEAN', 'CD_CONTA', 'VL_REAL']]
                dfc_calc = dfp_dfc_anual.merge(dfc_9m, on=['CNPJ_CLEAN', 'CD_CONTA'], how='left')
                cnpjs_sem_9m_dfc = set(dfp_dfc_anual['CNPJ_CLEAN'].unique()) - set(dfc_9m['CNPJ_CLEAN'].unique())
                dfc_calc['VL_Q4'] = dfc_calc['VL_REAL'] - dfc_calc['VL_9M']
                if cnpjs_sem_9m_dfc:
                    dfc_calc.loc[dfc_calc['CNPJ_CLEAN'].isin(cnpjs_sem_9m_dfc), 'VL_Q4'] = float('nan')

                dfc_q4_final = self.agrupar_contas_fluxo(dfc_calc, 'VL_Q4')
                # Bug D: sanity check D&A Q4 acumulado
                dfc_q4_final = self._sanity_check_da_q4(dfc_q4_final, resultados)

            if not patrimonio_q4.empty:
                q4_df = patrimonio_q4.merge(dre_q4_final, on='CNPJ_CLEAN', how='left') \
                                     .merge(dfc_q4_final, on='CNPJ_CLEAN', how='left')

                q4_df['DT_FIM_EXERC'] = dt_q4
                q4_df['DT_INI_TRIM'] = dt_ini_q4
                resultados.append(q4_df)

        # Limpar cache
        self.limpar_cache_ano(ano)

        if not resultados:
            return pd.DataFrame()

        df_final = pd.concat(resultados, ignore_index=True)

        # Adicionar nomes das empresas
        nomes = itr_bpa[['CNPJ_CLEAN', 'DENOM_CIA', 'CNPJ_CIA']].drop_duplicates('CNPJ_CLEAN')
        df_final = df_final.merge(nomes, on='CNPJ_CLEAN', how='left')

        self._update_progress(f"✓ Ano {ano} processado ({len(df_final)} registros)")

        return df_final

    @staticmethod
    def _sanity_check_da_q4(dfc_q4_final: pd.DataFrame, resultados_q123: list) -> pd.DataFrame:
        """
        Bug D: se DA Q4 > 3x mediana de DA Q1-Q3 do mesmo ano → setar DA_Trimestral = NaN.

        Args:
            dfc_q4_final: DataFrame com DFC do Q4 (saída de agrupar_contas_fluxo)
            resultados_q123: Lista de DataFrames dos trimestres Q1-Q3

        Returns:
            dfc_q4_final com DA_Trimestral corrigido
        """
        if dfc_q4_final.empty or 'DA_Trimestral' not in dfc_q4_final.columns:
            return dfc_q4_final

        if not resultados_q123:
            return dfc_q4_final

        # Consolidar Q1-Q3 e calcular mediana de DA_Trimestral por CNPJ
        try:
            df_q123 = pd.concat(
                [r[['CNPJ_CLEAN', 'DA_Trimestral']] for r in resultados_q123
                 if not r.empty and 'DA_Trimestral' in r.columns],
                ignore_index=True
            )
            if df_q123.empty:
                return dfc_q4_final

            mediana_da = df_q123.groupby('CNPJ_CLEAN')['DA_Trimestral'].median()
            dfc_q4_final = dfc_q4_final.copy()

            for cnpj in dfc_q4_final['CNPJ_CLEAN']:
                if cnpj not in mediana_da.index:
                    continue
                med = mediana_da[cnpj]
                da_q4 = dfc_q4_final.loc[dfc_q4_final['CNPJ_CLEAN'] == cnpj, 'DA_Trimestral']
                if da_q4.empty or pd.isna(da_q4.values[0]) or pd.isna(med) or med == 0:
                    continue
                if abs(da_q4.values[0]) > 3 * abs(med):
                    dfc_q4_final.loc[dfc_q4_final['CNPJ_CLEAN'] == cnpj, 'DA_Trimestral'] = float('nan')
                    logging.info(f"[_sanity_check_da_q4] CNPJ {cnpj}: DA Q4 > 3x mediana Q1-Q3 → NaN")
        except Exception as e:
            logging.warning(f"[_sanity_check_da_q4] Erro no sanity check: {e}")

        return dfc_q4_final

    # Continua na próxima mensagem...

    # ==========================================================================
    # ENRIQUECIMENTO COM MERCADO (YAHOO FINANCE)
    # ==========================================================================

    def _baixar_precos_ticker(self, ticker_sa: str, data_min: pd.Timestamp,
                              data_max: pd.Timestamp) -> pd.DataFrame:
        """
        Baixa histórico de preços de um ticker no período completo.
        Retorna DataFrame indexado por data com coluna 'Close'.
        """
        import time as _time

        start = data_min - timedelta(days=20)
        end = data_max + timedelta(days=5)

        try:
            # Suprimir logs de ERROR do yfinance para tickers deslistados
            yf_logger = logging.getLogger('yfinance')
            prev_level = yf_logger.level
            yf_logger.setLevel(logging.CRITICAL)
            try:
                h = yf.download(ticker_sa, start=start, end=end,
                               progress=False, auto_adjust=True)
            finally:
                yf_logger.setLevel(prev_level)

            if h.empty:
                logging.info(f"[yfinance] {ticker_sa}: sem dados (possivelmente deslistado)")
                return pd.DataFrame()

            # Tratar MultiIndex (yfinance pode retornar colunas multi-nível)
            if hasattr(h.columns, 'nlevels') and h.columns.nlevels > 1:
                h.columns = h.columns.get_level_values(0)

            if 'Close' not in h.columns:
                return pd.DataFrame()

            return h[['Close']].copy()

        except Exception as e:
            self._update_progress(f"  ⚠️ Erro download {ticker_sa}: {str(e)[:60]}", 0)
            return pd.DataFrame()

    def _obter_info_ticker(self, ticker_sa: str) -> dict:
        """
        Obtém informações fundamentais de um ticker (sharesOutstanding etc).
        Retorna dicionário com info ou {} se falhar.
        """
        try:
            yf_logger = logging.getLogger('yfinance')
            prev_level = yf_logger.level
            yf_logger.setLevel(logging.CRITICAL)
            try:
                tk = yf.Ticker(ticker_sa)
                info = tk.info or {}
            finally:
                yf_logger.setLevel(prev_level)
            return info
        except Exception as e:
            self._update_progress(f"  ⚠️ Erro info {ticker_sa}: {str(e)[:60]}", 0)
            return {}

    def enriquecer_com_mercado(self, df: pd.DataFrame, map_tickers: dict,
                              map_tipos: dict) -> pd.DataFrame:
        """
        Enriquece dados com preços do Yahoo Finance.
        Estratégia otimizada: baixa preços por ticker único (não por linha),
        com cache e delay entre requests para evitar rate limiting (429).

        Args:
            df: DataFrame com dados contábeis
            map_tickers: Dicionário CNPJ -> Ticker
            map_tipos: Dicionário CNPJ -> Tipo/Setor

        Returns:
            DataFrame enriquecido
        """
        import time as _time

        self._update_progress("🌍 Iniciando enriquecimento com Yahoo Finance...")

        df['Ticker'] = df['CNPJ_CLEAN'].map(map_tickers)
        df['Tipo'] = df['CNPJ_CLEAN'].map(map_tipos)

        # Bug C: deduplicar por ['Ticker', 'DT_FIM_EXERC'] mantendo maior Ativo Total
        # Apenas quando Ticker não é NaN (empresas sem ticker ficam intactas)
        if 'Ativo Total' in df.columns:
            mask_com_ticker = df['Ticker'].notna()
            df_com_ticker = df[mask_com_ticker].copy()
            df_sem_ticker = df[~mask_com_ticker].copy()
            df_com_ticker = (
                df_com_ticker
                .sort_values('Ativo Total', ascending=False)
                .drop_duplicates(subset=['Ticker', 'DT_FIM_EXERC'], keep='first')
                .sort_values(['Ticker', 'DT_FIM_EXERC'])
                .reset_index(drop=True)
            )
            df = pd.concat([df_com_ticker, df_sem_ticker], ignore_index=True)

        # Suprimir apenas warnings de FutureWarning, NÃO erros
        warnings.simplefilter('ignore', FutureWarning)

        # Calcular EBITDA
        df['EBITDA'] = (df['Lucro Liquido'].fillna(0) -
                       df['Res_Fin'].fillna(0) -
                       df['IR'].fillna(0) +
                       df['DA_Trimestral'].fillna(0))

        # Item 4: Bancos e Seguradoras — EBITDA e D&A não fazem sentido para Financeiro
        if 'Tipo' in df.columns:
            financial_mask = df['Tipo'] == 'Financeiro'
            df.loc[financial_mask, 'EBITDA'] = float('nan')
            df.loc[financial_mask, 'DA_Trimestral'] = float('nan')

        # ── Identificar tickers únicos e seus intervalos de datas ──────
        tickers_unicos = df[df['Ticker'].notna()]['Ticker'].unique()
        total_tickers = len(tickers_unicos)
        self._update_progress(f"  📋 {total_tickers} tickers únicos para buscar preços")

        # Cache: ticker -> DataFrame de preços históricos
        cache_precos = {}
        # Cache: ticker -> dict info (sharesOutstanding etc)
        cache_info = {}

        precos_ok = 0
        precos_fail = 0

        for i, ticker in enumerate(tickers_unicos, 1):
            t_sa = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker

            # Encontrar intervalo de datas para este ticker
            mask_ticker = df['Ticker'] == ticker
            datas = df.loc[mask_ticker, 'DT_FIM_EXERC']
            data_min = datas.min()
            data_max = datas.max()

            # Baixar preços históricos (uma chamada por ticker)
            hist = self._baixar_precos_ticker(t_sa, data_min, data_max)
            if not hist.empty:
                cache_precos[ticker] = hist
                precos_ok += 1
            else:
                precos_fail += 1

            # Rate limiting: esperar 1s entre requests
            _time.sleep(1.0)

            # Obter info (sharesOutstanding)
            info = self._obter_info_ticker(t_sa)
            if info:
                cache_info[ticker] = info

            # Rate limiting: esperar 1s entre requests
            _time.sleep(1.0)

            # Progresso a cada 5% ou a cada 10 tickers
            if i % max(1, total_tickers // 20) == 0 or i <= 3:
                pct = i / total_tickers
                self._update_progress(
                    f"  📈 {i}/{total_tickers} tickers ({pct:.0%}) "
                    f"[preços: {precos_ok}, falhas: {precos_fail}]", 0
                )

        self._update_progress(
            f"  ✓ Downloads finalizados: {precos_ok} OK, {precos_fail} falhas "
            f"de {total_tickers} tickers"
        )

        # ── Mapear preços e market cap para cada linha do DataFrame ────
        preco_list = []
        mcap_list = []
        acoes_list = []

        for row in df.itertuples():
            t = row.Ticker
            dt_f = row.DT_FIM_EXERC
            p_fechamento, mc, shares_mm = np.nan, np.nan, np.nan

            if pd.notna(t) and pd.notna(dt_f) and t in cache_precos:
                hist = cache_precos[t]

                # Encontrar o preço mais próximo da data de referência
                # Janela: 15 dias antes até a data
                start_win = dt_f - timedelta(days=15)
                end_win = dt_f + timedelta(days=1)

                hist_janela = hist[(hist.index >= start_win) & (hist.index <= end_win)]

                if not hist_janela.empty:
                    val = hist_janela['Close'].iloc[-1]
                    if isinstance(val, pd.Series):
                        val = val.iloc[0]
                    try:
                        p_fechamento = float(val)
                    except (TypeError, ValueError):
                        pass

                # Market Cap via sharesOutstanding do cache
                if pd.notna(p_fechamento) and t in cache_info:
                    shares = cache_info[t].get('sharesOutstanding')
                    if shares:
                        mc = p_fechamento * shares
                        shares_mm = shares / 1_000_000

            preco_list.append(p_fechamento)
            mcap_list.append(mc)
            acoes_list.append(shares_mm)

        df['Preco_Fechamento'] = preco_list
        df['Market_Cap'] = mcap_list
        df['Qtd_Acoes_Milhoes'] = acoes_list

        # Estatísticas finais
        precos_preenchidos = df['Preco_Fechamento'].notna().sum()
        mcap_preenchidos = df['Market_Cap'].notna().sum()
        self._update_progress(
            f"  📊 Preços preenchidos: {precos_preenchidos}/{len(df)} linhas | "
            f"Market Cap: {mcap_preenchidos}/{len(df)} linhas"
        )

        # Cálculos de múltiplos
        df['EV'] = df['Market_Cap'].fillna(0) + df['Divida Liquida'].fillna(0)
        df['P_E'] = df['Market_Cap'] / (df['Lucro Liquido'] * 4)
        df['EV_EBITDA'] = df['EV'] / (df['EBITDA'] * 4)
        df['Price_to_Book'] = df['Market_Cap'] / df['Patrimonio Liquido']

        # DL/EV (evitar divisão por zero)
        df['DL_EV'] = df.apply(
            lambda row: row['Divida Liquida'] / row['EV']
            if row['EV'] and row['EV'] != 0 else np.nan,
            axis=1
        )

        warnings.simplefilter('default', FutureWarning)

        self._update_progress("✓ Enriquecimento completo")
        return df

    # ==========================================================================
    # RESUMOS (SETORES + MERCADO)
    # ==========================================================================

    @staticmethod
    def _safe_median(s):
        """Calcula mediana ignorando inf/nan."""
        s = pd.to_numeric(s, errors="coerce")
        s = s.replace([np.inf, -np.inf], np.nan).dropna()
        return s.median() if not s.empty else np.nan

    @staticmethod
    def _safe_sum(s):
        """Calcula soma ignorando inf/nan."""
        s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan)
        return np.nan_to_num(s, nan=0.0).sum()

    @staticmethod
    def _weighted_pe(market_cap, lucro):
        """Calcula P/E ponderado."""
        mc = pd.to_numeric(market_cap, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
        ll = pd.to_numeric(lucro, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
        ll_pos = ll.where(ll > 0, 0.0)
        denom = 4.0 * ll_pos.sum()
        return mc.sum() / denom if denom > 0 else np.nan

    @staticmethod
    def _weighted_ev_ebitda(ev, ebitda):
        """Calcula EV/EBITDA ponderado."""
        evv = pd.to_numeric(ev, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
        eb = pd.to_numeric(ebitda, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
        eb_pos = eb.where(eb > 0, 0.0)
        denom = 4.0 * eb_pos.sum()
        return evv.sum() / denom if denom > 0 else np.nan

    def gerar_resumos_snapshot(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Gera resumos setoriais e de mercado (snapshot).

        Args:
            df: DataFrame completo

        Returns:
            Tuple (resumo_setores, resumo_mercado)
        """
        if df.empty or "DT_FIM_EXERC" not in df.columns:
            return pd.DataFrame(), pd.DataFrame()

        snapshot_date = df["DT_FIM_EXERC"].max()
        snap = df[df["DT_FIM_EXERC"] == snapshot_date].copy()

        if "Tipo" not in snap.columns:
            snap["Tipo"] = np.nan

        snap["Tipo"] = snap["Tipo"].replace("", np.nan)

        # Resumo Setores
        setores = (
            snap.dropna(subset=["Tipo"])
            .groupby("Tipo", dropna=True)
            .apply(lambda g: pd.Series({
                "DT_FIM_EXERC": snapshot_date,
                "N_Empresas": g["Ticker"].nunique() if "Ticker" in g.columns else len(g),
                "Market_Cap_Sum": self._safe_sum(g["Market_Cap"]),
                "EV_Sum": self._safe_sum(g["EV"]),
                "Lucro_Sum": self._safe_sum(g["Lucro Liquido"]),
                "EBITDA_Sum": self._safe_sum(g["EBITDA"]),
                "Price_to_Book_Median": self._safe_median(g["Price_to_Book"]),
                "P_E_Median": self._safe_median(g["P_E"]),
                "EV_EBITDA_Median": self._safe_median(g["EV_EBITDA"]),
                "P_E_Agregado": self._weighted_pe(g.get("Market_Cap"), g.get("Lucro Liquido")),
                "EV_EBITDA_Agregado": self._weighted_ev_ebitda(g.get("EV"), g.get("EBITDA")),
            }))
            .reset_index()
            .rename(columns={"Tipo": "SETOR"})
        )

        # Resumo Mercado
        mercado = pd.DataFrame([{
            "DT_FIM_EXERC": snapshot_date,
            "N_Empresas": snap["Ticker"].nunique() if "Ticker" in snap.columns else len(snap),
            "Market_Cap_Sum": self._safe_sum(snap["Market_Cap"]),
            "EV_Sum": self._safe_sum(snap["EV"]),
            "Lucro_Sum": self._safe_sum(snap["Lucro Liquido"]),
            "EBITDA_Sum": self._safe_sum(snap["EBITDA"]),
            "Price_to_Book_Median": self._safe_median(snap["Price_to_Book"]),
            "P_E_Median": self._safe_median(snap["P_E"]),
            "EV_EBITDA_Median": self._safe_median(snap["EV_EBITDA"]),
            "P_E_Agregado": self._weighted_pe(snap.get("Market_Cap"), snap.get("Lucro Liquido")),
            "EV_EBITDA_Agregado": self._weighted_ev_ebitda(snap.get("EV"), snap.get("EBITDA")),
        }])

        return setores, mercado

    # ==========================================================================
    # EXPORT
    # ==========================================================================

    def gerar_parquet(self, df: pd.DataFrame):
        """
        Gera os 3 arquivos Parquet resultantes do pipeline.

        Args:
            df: DataFrame completo com dados enriquecidos
        """
        from config.settings import PARQUET_BASE_FILE, PARQUET_SETORES_FILE, PARQUET_MERCADO_FILE

        self._update_progress("💾 Gerando arquivos Parquet...")

        # Garantir diretório criado
        PARQUET_BASE_FILE.parent.mkdir(parents=True, exist_ok=True)

        cols = ['CNPJ_CIA', 'DENOM_CIA', 'Ticker', 'Tipo', 'DT_FIM_EXERC',
                # Ativo
                'Ativo Total', 'Ativo Circulante', 'Caixa', 'Aplicacoes Financeiras',
                'Contas a Receber', 'Estoques', 'Ativo Nao Circulante',
                'Imobilizado', 'Intangivel',
                # Passivo
                'Passivo Total', 'Passivo Circulante', 'Passivo Nao Circulante',
                'Divida Bruta', 'Divida Liquida', 'Patrimonio Liquido',
                # DRE
                'Receita_Liquida', 'CPV', 'Lucro_Bruto', 'Despesas_Operacionais', 'EBIT',
                'Lucro Liquido', 'EBITDA', 'Res_Fin', 'IR', 'DA_Trimestral',
                # DFC
                'FCO', 'FCI', 'FCF',
                'Caixa_Gerado_Ops', 'Var_Ativos_Passivos', 'Outros_Operacional',
                'Var_Cambial', 'Var_Liquida_Caixa', 'Saldo_Inicial_Caixa', 'Saldo_Final_Caixa',
                # Mercado
                'Preco_Fechamento', 'Qtd_Acoes_Milhoes',
                'Market_Cap', 'EV', 'P_E', 'EV_EBITDA', 'Price_to_Book', 'DL_EV']

        df_export = df[[c for c in cols if c in df.columns]].copy()

        # Salvar Base
        df_export.to_parquet(PARQUET_BASE_FILE, index=False)

        # Gerar Resumos e salvar
        resumo_setores, resumo_mercado = self.gerar_resumos_snapshot(df)

        if not resumo_setores.empty:
            resumo_setores.to_parquet(PARQUET_SETORES_FILE, index=False)
            
        if not resumo_mercado.empty:
            resumo_mercado.to_parquet(PARQUET_MERCADO_FILE, index=False)

        self._update_progress("✓ Parquets salvos com sucesso!")

    # ==========================================================================
    # EXECUÇÃO PRINCIPAL
    # ==========================================================================

    def run_full_pipeline(self) -> pd.DataFrame:
        """
        Executa pipeline completo (modo normal).

        Returns:
            DataFrame final com todos os dados
        """
        # Calcular total de steps
        anos = list(range(self.ano_inicio, self.ano_fim + 1))
        self.total_steps = (
            1 +  # setup
            1 +  # carregar tickers
            len(anos) * 10 +  # processar anos (múltiplos steps por ano)
            20 +  # enriquecimento
            5    # export
        )
        self.current_step = 0

        # Setup
        self.setup_directories()

        # Carregar tickers
        map_tickers, map_tipos = self.carregar_tickers_e_tipos()

        if not map_tickers:
            self._update_progress("❌ Sem tickers, abortando")
            return pd.DataFrame()

        # Processar anos
        dfs = []
        for ano in anos:
            df_ano = self.processar_ano_completo(ano)
            if not df_ano.empty:
                dfs.append(df_ano)

        if not dfs:
            self._update_progress("❌ Nenhum dado processado")
            return pd.DataFrame()

        # Concatenar
        self._update_progress("🔗 Consolidando dados...")
        full_df = pd.concat(dfs, ignore_index=True)

        # Enriquecer
        final_df = self.enriquecer_com_mercado(full_df, map_tickers, map_tipos)

        # Exportar
        self.gerar_parquet(final_df)

        self._update_progress("✅ Pipeline completo!", 0)

        return final_df

    def run_incremental_pipeline(self, quarters_to_process: list) -> pd.DataFrame:
        """
        Executa pipeline incremental.

        Args:
            quarters_to_process: Lista de (ano, trimestre) a processar

        Returns:
            DataFrame com novos dados
        """
        from config.settings import PARQUET_BASE_FILE
        import os
        from datetime import datetime
        import shutil

        self._update_progress("🔄 Iniciando pipeline incremental...")

        # Verificar se Parquet mestre existe
        if not PARQUET_BASE_FILE.exists():
            self._update_progress("❌ Parquet base não encontrado. Execute pipeline completo primeiro.")
            return pd.DataFrame()

        # Criar backup do Parquet
        backup_dir = PARQUET_BASE_FILE.parent / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_name = f"base_consolidada_{datetime.now().strftime('%Y%m%d_%H%M%S')}_backup.parquet"
        backup_path = backup_dir / backup_name

        self._update_progress("💾 Criando backup...")
        shutil.copy2(PARQUET_BASE_FILE, backup_path)

        # Carregar dados existentes
        self._update_progress("📖 Carregando dados existentes...")
        df_existing = pd.read_parquet(PARQUET_BASE_FILE)

        # Carregar mapeamentos
        self._update_progress("📋 Carregando tickers...")
        map_tickers, map_tipos = self.carregar_tickers_e_tipos()

        # Processar apenas trimestres novos
        self.total_steps = len(quarters_to_process) * 10 + 10
        self.current_step = 0

        new_dfs = []

        for i, (ano, trimestre) in enumerate(quarters_to_process):
            self._update_progress(f"📊 Processando Q{trimestre} {ano}...", step_increment=1)

            try:
                # Processar ano completo (inclui o trimestre desejado)
                df_ano = self.processar_ano_completo(ano)

                if df_ano.empty:
                    continue

                # Filtrar apenas o trimestre desejado
                quarter_end_month = trimestre * 3
                df_trimestre = df_ano[df_ano['DT_FIM_EXERC'].dt.month == quarter_end_month].copy()

                if not df_trimestre.empty:
                    new_dfs.append(df_trimestre)
                    self._update_progress(f"✅ Q{trimestre} {ano} processado: {len(df_trimestre)} registros")

            except Exception as e:
                self._update_progress(f"⚠️ Erro em Q{trimestre} {ano}: {str(e)}")
                continue

        if not new_dfs:
            self._update_progress("❌ Nenhum dado novo processado")
            return pd.DataFrame()

        # Consolidar novos dados
        self._update_progress("🔗 Consolidando novos dados...")
        df_new = pd.concat(new_dfs, ignore_index=True)

        # Enriquecer com dados de mercado
        self._update_progress("📈 Enriquecendo com Yahoo Finance...")
        df_new_enriched = self.enriquecer_com_mercado(df_new, map_tickers, map_tipos)

        # Merge com dados existentes
        self._update_progress("🔀 Mesclando com dados existentes...")

        # Concatenar
        df_combined = pd.concat([df_existing, df_new_enriched], ignore_index=True)

        # Remover duplicatas (por CNPJ + Data)
        df_combined = df_combined.drop_duplicates(subset=['CNPJ_CIA', 'DT_FIM_EXERC'], keep='last')

        # Ordenar por data
        df_combined = df_combined.sort_values('DT_FIM_EXERC').reset_index(drop=True)

        # Exportar atualizado
        self._update_progress("💾 Salvando Parquets atualizados...")
        self.gerar_parquet(df_combined)

        self._update_progress(f"✅ Pipeline incremental concluído! {len(df_new_enriched)} novos registros adicionados.")

        return df_new_enriched
