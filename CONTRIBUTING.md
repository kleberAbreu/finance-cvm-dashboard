# Contribuindo

Obrigado por considerar contribuir com o Finance CVM Dashboard.

## Como Rodar Localmente

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pytest
streamlit run app.py
```

O projeto inclui dados de amostra em `data/sample/`, então o dashboard abre sem
baixar a base completa.

## Antes de Enviar Mudanças

```bash
python -m compileall app.py config src pages tests
pytest -q
```

## Boas Práticas

- Mantenha os dados completos gerados pelo pipeline fora do Git.
- Não adicione credenciais, tokens, arquivos `.env` ou configs privadas.
- Preserve nomes de colunas usados pelo dashboard ao mexer no pipeline.
- Inclua testes quando alterar carregamento, filtros, cálculos ou pipeline.

## Issues e Pull Requests

Ao reportar problemas, inclua:

- Sistema operacional e versão do Python.
- Comando executado.
- Mensagem de erro completa.
- Se o erro ocorre com a amostra pública ou com dados gerados localmente.
