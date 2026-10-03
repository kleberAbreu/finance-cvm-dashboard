# Finance CVM — apresentação editorial

O relatório público adota uma linguagem editorial para leitura de fundamentos financeiros: papel claro, azul profundo, verde discreto e títulos em serif. O objetivo é hierarquia e clareza nas sete telas de análise.

## Tokens e fundamentos

- Fundo: `#f5f5f0`; superfície: `#ffffff`; texto: `#102f42`; secundário: `#536674`; ação: `#14796e`; borda: `#dfe5df`.
- Instrument Serif nos títulos; Manrope na interface e nos gráficos. Fontes locais e respectivas licenças em `assets/fonts`; nenhuma requisição externa de fontes.
- Espaçamento baseado em 8 px; bordas de 5–7 px; quatro indicadores na visão geral. Valores se ajustam à largura real de cada card.

## Componentes e estados

- Navegação registrada no Streamlit, com sete links nativos e indicação da página ativa. Os filtros mantêm suas chaves, padrões e cálculos.
- Indicadores usam unidades compactas; gráficos mantêm dados, rótulos e unidades originais. Normalização base 100 e variação percentual não recebem unidades monetárias.
- Superfícies claras para gráficos e tabelas; destaques discretos em verde; negativos nas demonstrações em vermelho escuro.
- Downloads nativos e filtros acessíveis; seleções predefinidas ainda não implementadas aparecem desabilitadas com contexto explícito.
- Hover discreto e foco visível de 3 px. Transições respeitam `prefers-reduced-motion`.

## Acessibilidade e conteúdo

- Títulos claros, um título principal por tela e descrições curtas. Emojis decorativos foram removidos dos principais títulos.
- Texto e ações em cores de contraste alto. Usar teclado para navegar, selecionar filtros e acionar downloads; não ocultar controles nativos de navegação mobile.
- Em telas estreitas, o Streamlit empilha as colunas; tabelas preservam sua rolagem própria. Verificar ausência de rolagem horizontal da página em 390 e 320 px.
- A amostra congelada permanece explicitamente demonstrativa. Não apresentar os valores como cotações atuais ou evidência de rentabilidade.

## Verificação de publicação

- Executar testes, compilação e checagem de dependências.
- Renderizar as sete páginas; abrir demonstrações com uma empresa selecionada.
- Conferir normalização e filtro de empresa, exportações, largura mobile, navegação e foco.
- Publicar uma release isolada, manter rollback e verificar HTTPS, saúde do serviço e correspondência com o commit publicado.
