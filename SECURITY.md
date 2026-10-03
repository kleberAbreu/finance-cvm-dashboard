# Política de Segurança

## Versões Suportadas

Enquanto o projeto estiver em fase inicial, apenas a branch `main` recebe
correções de segurança.

## Reporte de Vulnerabilidades

Abra uma issue apenas para problemas que não exponham credenciais ou dados
sensíveis. Para vulnerabilidades sensíveis, entre em contato diretamente com o
mantenedor do repositório pelo perfil do GitHub antes de publicar detalhes.

## Dados e Credenciais

- O dashboard roda localmente sem login por padrão.
- Autenticação é opcional para deploys privados e deve ser configurada fora do Git.
- Arquivos como `.env`, `auth_config.yaml`, `secrets.toml` e credenciais cloud
  não devem ser commitados.
- A base completa gerada pelo pipeline deve permanecer fora do repositório.

## Aviso Financeiro

Este projeto é uma ferramenta educacional e analítica. Ele não oferece
recomendação de investimento, consultoria financeira, contábil ou jurídica.
