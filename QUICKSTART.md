# Guia Rápido

## Rodar Em 3 Passos

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Abra `http://localhost:8501`.

O dashboard abre sem login e usa os dados de amostra em `data/sample/` quando a
base completa ainda não existe.

## Usar Dados Completos

```bash
python run_pipeline.py --inicio 2018 --fim 2025
streamlit run app.py
```

Os Parquets gerados ficam em `pipeline_cvm_final/outputs/` e não devem ser
commitados.

## Verificação

```bash
python -m compileall app.py config src pages tests
pytest -q
```

## Problemas Comuns

### Dependência ausente

```bash
python -m pip install -r requirements.txt
```

### App abriu com amostra, mas você queria dados reais

Confirme se estes arquivos existem:

```bash
ls -lh pipeline_cvm_final/outputs/*.parquet
```

Se não existirem, execute `python run_pipeline.py`.

### Dashboard lento

- Use "Apenas trimestre mais recente".
- Limite o "Top N por Market Cap".
- Reduza o intervalo de datas.
