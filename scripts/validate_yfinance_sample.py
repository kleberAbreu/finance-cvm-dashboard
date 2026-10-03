#!/usr/bin/env python3
"""
Teste de validação do enriquecimento Yahoo Finance.
Testa 5 tickers conhecidos com delay entre requests para evitar 429.

Uso:
    python3 test_enrich_sample.py
"""
import sys
import time
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# ── Tickers de teste (grandes e líquidos) ───────────────────────────────────
TICKERS_TESTE = ["PETR4.SA", "VALE3.SA", "BBAS3.SA", "ITUB4.SA", "WEGE3.SA"]

# Data de referência: fim do último trimestre com dados disponíveis
DATA_REF = pd.Timestamp("2024-09-30")
DELAY_ENTRE_REQUESTS = 2.0  # segundos entre cada chamada


def testar_download(ticker: str, data_ref: pd.Timestamp) -> dict:
    """Testa yf.download() e yf.Ticker().info para um ticker."""
    resultado = {
        "ticker": ticker, "preco": np.nan, "market_cap": np.nan,
        "shares": np.nan, "erro": None, "linhas_hist": 0,
    }

    start_win = data_ref - timedelta(days=15)
    end_win = data_ref + timedelta(days=1)

    print(f"\n{'='*60}")
    print(f"  🔍 {ticker}  |  {start_win.date()} → {end_win.date()}")
    print(f"{'='*60}")

    # ── Download preços ────────────────────────────────────────────────
    try:
        h = yf.download(ticker, start=start_win, end=end_win,
                        progress=False, auto_adjust=True)

        # Tratar MultiIndex
        if hasattr(h.columns, 'nlevels') and h.columns.nlevels > 1:
            h.columns = h.columns.get_level_values(0)

        resultado["linhas_hist"] = len(h)
        print(f"  📊 Shape: {h.shape} | Colunas: {list(h.columns)}")

        if not h.empty and 'Close' in h.columns:
            val = h['Close'].iloc[-1]
            if isinstance(val, pd.Series):
                val = val.iloc[0]
            resultado["preco"] = float(val)
            print(f"  💰 Preço: R$ {resultado['preco']:.2f}")
            print(f"  📈 Últimas linhas:")
            print(h.tail(3).to_string(prefix="       "))
        else:
            print(f"  ⚠️  DataFrame vazio ou sem coluna Close!")

    except Exception as e:
        resultado["erro"] = str(e)
        print(f"  ❌ Erro download: {e}")

    # Delay antes do próximo request
    print(f"  ⏳ Aguardando {DELAY_ENTRE_REQUESTS}s...")
    time.sleep(DELAY_ENTRE_REQUESTS)

    # ── Info do ticker (sharesOutstanding) ──────────────────────────────
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        shares = info.get('sharesOutstanding')
        mc_yahoo = info.get('marketCap')
        resultado["shares"] = shares
        resultado["market_cap"] = mc_yahoo
        print(f"  📊 sharesOutstanding: {shares}")
        print(f"  📊 marketCap: {mc_yahoo}")
        print(f"  📊 shortName: {info.get('shortName', 'N/A')}")

        if shares and pd.notna(resultado["preco"]):
            mc_calc = resultado["preco"] * shares
            print(f"  📊 Market Cap (calc): R$ {mc_calc:,.0f}")

    except Exception as e:
        if not resultado["erro"]:
            resultado["erro"] = str(e)
        print(f"  ❌ Erro info: {e}")

    # Delay antes do próximo ticker
    print(f"  ⏳ Aguardando {DELAY_ENTRE_REQUESTS}s...")
    time.sleep(DELAY_ENTRE_REQUESTS)

    return resultado


def main():
    print("=" * 60)
    print("  🧪 VALIDAÇÃO YAHOO FINANCE (com rate limiting)")
    print(f"  📅 Referência: {DATA_REF.date()}")
    print(f"  🐍 Python {sys.version.split()[0]} | yfinance {yf.__version__}")
    print(f"  ⏱️  Delay: {DELAY_ENTRE_REQUESTS}s entre requests")
    print("=" * 60)

    resultados = []
    for ticker in TICKERS_TESTE:
        r = testar_download(ticker, DATA_REF)
        resultados.append(r)

    # ── Resumo ──────────────────────────────────────────────────────────
    df = pd.DataFrame(resultados)
    precos_ok = df["preco"].notna().sum()
    mcap_ok = df["market_cap"].notna().sum()

    print(f"\n\n{'='*60}")
    print(f"  📊 RESUMO")
    print(f"{'='*60}")
    print(f"\n  {'Ticker':<12} {'Preço':>12} {'Market Cap':>18} {'Status'}")
    print(f"  {'-'*12} {'-'*12} {'-'*18} {'-'*10}")
    for r in resultados:
        p = f"R$ {r['preco']:.2f}" if pd.notna(r['preco']) else "NaN"
        mc = f"{r['market_cap']:,.0f}" if pd.notna(r['market_cap']) else "NaN"
        st = "✅" if pd.notna(r['preco']) else f"❌ {(r['erro'] or '')[:30]}"
        print(f"  {r['ticker']:<12} {p:>12} {mc:>18} {st}")

    print(f"\n  Preços: {precos_ok}/{len(TICKERS_TESTE)} | Market Cap: {mcap_ok}/{len(TICKERS_TESTE)}")

    if precos_ok >= 4:
        print("\n  ✅ VALIDAÇÃO OK — pode executar o pipeline completo!")
    elif precos_ok > 0:
        print("\n  ⚠️  PARCIAL — alguns tickers falharam, mas enriquecimento funciona.")
    else:
        print("\n  ❌ FALHOU — nenhum preço obtido!")
        print("    Tente: pip install -U yfinance")
    print("=" * 60)

    return precos_ok


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result >= 4 else 1)
