# Pipeline Incremental

O pipeline incremental adiciona novos trimestres à base completa já gerada em
Parquet. Ele não é aplicado à amostra pública de `data/sample/`.

## Quando Usar

Use o incremental quando:

- Você já executou o pipeline completo ao menos uma vez.
- Os arquivos em `pipeline_cvm_final/outputs/` existem.
- Você quer adicionar apenas os trimestres mais recentes.

Use o pipeline completo quando:

- É a primeira execução.
- As fórmulas ou o mapeamento de tickers mudaram.
- Você suspeita de dados corrompidos.
- Quer reprocessar todo o histórico.

## Arquivos Atualizados

- `pipeline_cvm_final/outputs/base_consolidada.parquet`
- `pipeline_cvm_final/outputs/resumo_setores.parquet`
- `pipeline_cvm_final/outputs/resumo_mercado.parquet`

Antes de atualizar a base, o pipeline cria backup em:

```text
pipeline_cvm_final/outputs/backups/
```

Esses arquivos são locais e não devem ser commitados.

## Executar

Pelo dashboard:

```text
Página "Pipeline Execution" → Executar Pipeline Incremental
```

Pelo terminal, use o pipeline completo quando precisar reconstruir tudo:

```bash
python run_pipeline.py --inicio 2018 --fim 2025
```

## Calendário Prático

| Trimestre | Divulgação típica | Processar a partir de |
|-----------|-------------------|------------------------|
| Q1        | Maio              | Junho                  |
| Q2        | Agosto            | Setembro               |
| Q3        | Novembro          | Dezembro               |
| Q4        | Março seguinte    | Abril                  |

## Validação Depois De Atualizar

```bash
python -m compileall app.py config src pages tests
pytest -q
```

Depois abra o dashboard e confira:

- O trimestre novo aparece nos filtros.
- A página Overview mostra métricas sem erros.
- Uma empresa conhecida mostra o novo período no P&L.
- Valores amostrais batem com fontes públicas usadas pelo pipeline.
