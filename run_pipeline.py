#!/usr/bin/env python3
"""
Executa o pipeline completo CVM + Yahoo Finance via terminal.

Uso:
    python3 run_pipeline.py                  # Pipeline completo (2015-2025)
    python3 run_pipeline.py --inicio 2020    # A partir de 2020
    python3 run_pipeline.py --fim 2024       # Até 2024
"""
import argparse
import sys
import time
from datetime import datetime
from config.settings import ANO_FIM_DEFAULT, ANO_INICIO_DEFAULT


def main():
    parser = argparse.ArgumentParser(description="Pipeline CVM + Yahoo Finance")
    parser.add_argument("--inicio", type=int, default=ANO_INICIO_DEFAULT, help=f"Ano inicial (default: {ANO_INICIO_DEFAULT})")
    parser.add_argument("--fim", type=int, default=ANO_FIM_DEFAULT, help=f"Ano final (default: {ANO_FIM_DEFAULT})")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  🚀 Pipeline CVM — Processamento Completo")
    print(f"  📅 Período: {args.inicio} a {args.fim}")
    print(f"  🕐 Início: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    print()

    start_time = time.time()

    def progress_callback(pct, message):
        elapsed = time.time() - start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        bar_len = 30
        filled = int(bar_len * pct)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"  [{bar}] {pct:5.1%}  ⏱ {elapsed_str}  {message}")

    try:
        from src.data.pipeline_runner import PipelineRunner

        runner = PipelineRunner(
            ano_inicio=args.inicio,
            ano_fim=args.fim,
            progress_callback=progress_callback
        )

        df = runner.run_full_pipeline()

        elapsed = time.time() - start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))

        print()
        print("=" * 60)
        if not df.empty:
            print(f"  ✅ Pipeline concluído com sucesso!")
            print(f"  📊 {len(df)} registros processados")
            print(f"  🏢 {df['Ticker'].nunique()} empresas")
            print(f"  ⏱  Tempo total: {elapsed_str}")
            print(f"  💾 Parquets salvos em: pipeline_cvm_final/outputs/")
        else:
            print(f"  ❌ Pipeline finalizado sem dados.")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n  ⚠️  Pipeline interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
