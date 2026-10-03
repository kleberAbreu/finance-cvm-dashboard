# Publicação da demonstração

URL: https://www.kleberabreu.com.br/dashboard/

A aplicação pública usa `public_app.py`, sete páginas de análise e a amostra
congelada em `data/sample/`. O pipeline não é uma rota registrada. Os CSVs da
barra lateral e das demonstrações financeiras incluem fonte e unidade.

O serviço `finance-cvm-public.service` escuta somente em 127.0.0.1:8502, usa
usuário dinâmico, filesystem protegido e limites de recursos. As dependências
ficam em `/var/www/finance-cvm-public/venv/`; `current` aponta para uma release
preservada. A instância anterior em 8501 não é usada pela demonstração.

Nginx encaminha `/dashboard/` (incluindo WebSocket) sem remover o prefixo.
Streamlit recebe `--server.baseUrlPath dashboard`. O certificado é o mesmo do
portfólio. Para atualizar, validar os testes, instalar uma nova release, trocar
`current` atomicamente, reiniciar somente o serviço público e conferir as páginas
no navegador. Preserve a release anterior para rollback.

Verificação: 25 testes de schema/carregamento, filtros/cálculos, sete páginas,
reconciliação de KPIs com a amostra, exportação e isolamento do pipeline.
A geração de uma base CVM/Yahoo completa não foi executada neste lançamento.
