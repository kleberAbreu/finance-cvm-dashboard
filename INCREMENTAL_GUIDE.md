# 🔄 Guia do Pipeline Incremental

## O que é?

O **Pipeline Incremental** permite atualizar seus dados processando apenas os **novos trimestres**, sem reprocessar todo o histórico. Isso economiza horas de tempo!

## 📊 Comparação

| Característica | Pipeline Completo | Pipeline Incremental |
|----------------|-------------------|----------------------|
| **Tempo** | 3-4 horas | ~5 min/trimestre |
| **Processa** | 2015-2025 (completo) | Apenas novos trimestres |
| **Usa quando** | Primeira vez ou dados com problemas | Atualizações regulares |
| **Requisito** | Nenhum | Excel existente |

## 🎯 Como Usar

### 1. Acesse no Dashboard

```
Sidebar → Fonte de Dados → "Executar incremental"
```

### 2. Verifique Informações

O dashboard mostra:
- ✅ Último trimestre processado (ex: Q3 2025)
- 📊 Quantos trimestres novos disponíveis (ex: 2 trimestres)
- ⏱️ Tempo estimado (ex: 10-15 min vs 3-4h completo)
- 📋 Lista de trimestres a processar

### 3. Execute

Clique em **"▶️ Executar Incremental"**

O pipeline vai:
1. Detectar último trimestre processado
2. Baixar dados apenas dos novos trimestres da CVM
3. Processar e enriquecer com Yahoo Finance
4. Fazer append ao Excel existente
5. Atualizar resumos setoriais e de mercado

## 🔍 Exemplo Prático

### Cenário:
- Seu Excel atual vai até **Q3 2025**
- Hoje é **Janeiro 2026**
- Dados de Q4 2025 já estão disponíveis

### Resultado:
```
📊 Último trimestre processado: Q3 2025
✅ 1 trimestre novo disponível!

Trimestres a processar:
- Q4 2025

⏱️ Tempo estimado: 5-10 min (vs 3-4h completo)

[▶️ Executar Incremental]
```

## 📅 Quando Usar Cada Modo

### Use Pipeline Completo quando:
- ✅ É sua primeira execução (não tem Excel)
- ✅ Quer reprocessar tudo do zero
- ✅ Suspeita de dados corrompidos
- ✅ Mudou configurações importantes
- ✅ Quer dados de um período diferente

### Use Pipeline Incremental quando:
- ✅ Já tem Excel atualizado
- ✅ Quer apenas adicionar novos trimestres
- ✅ Faz atualizações regulares (a cada 3 meses)
- ✅ Quer economizar tempo
- ✅ Dados atuais estão corretos

## 🗓️ Calendário de Divulgação

Empresas brasileiras divulgam demonstrativos assim:

| Trimestre | Divulgação até | Processe a partir de |
|-----------|----------------|----------------------|
| Q1 (Jan-Mar) | Maio | Junho |
| Q2 (Abr-Jun) | Agosto | Setembro |
| Q3 (Jul-Set) | Novembro | Dezembro |
| Q4 (Out-Dez) | Março (ano seguinte) | Abril |

**Dica:** Execute o pipeline incremental ~1 mês após o fim do trimestre.

## 🛡️ Segurança dos Dados

### Backup Automático

Antes de executar o incremental, o sistema:
1. Cria backup do Excel existente
2. Salva em `pipeline_cvm_final/outputs/backups/`
3. Nome: `Valuation_Final_YYYYMMDD_backup.xlsx`

### Rollback

Se algo der errado:
```bash
# Restaurar backup manualmente
cp pipeline_cvm_final/outputs/backups/Valuation_Final_20260207_backup.xlsx \
   pipeline_cvm_final/outputs/Valuation_Final_20260207.xlsx
```

## 🔧 Lógica Técnica

### Como Funciona

1. **Detecção:**
   ```python
   # Lê Excel existente
   # Identifica última data: 2025-09-30
   # Extrai: Q3 2025
   ```

2. **Cálculo:**
   ```python
   # Data atual: 2026-01-15
   # Trimestre disponível mais recente: Q4 2025
   # Trimestres faltando: [Q4 2025]
   ```

3. **Processamento:**
   ```python
   # Para cada trimestre faltando:
   #   - Baixar ITR/DFP da CVM
   #   - Processar demonstrativos
   #   - Enriquecer com Yahoo Finance
   #   - Calcular múltiplos
   ```

4. **Merge:**
   ```python
   # Concatenar: [dados_existentes] + [dados_novos]
   # Remover duplicatas por (CNPJ, Data)
   # Ordenar por data
   # Salvar Excel atualizado
   ```

### Arquivos Modificados

O pipeline incremental atualiza:
- ✅ `Valuation_Final_YYYYMMDD.xlsx` (dados principais)
- ✅ Sheet "Base Consolidada" (append de linhas)
- ✅ Sheet "Resumo_Setores" (recalculado)
- ✅ Sheet "Resumo_Mercado" (recalculado)

## 📈 Benefícios

### Economia de Tempo

```
Atualização trimestral:
- Completo: 3-4 horas
- Incremental: 5-10 minutos
- Economia: 95% de tempo! ⚡
```

### Atualização Regular

```
Trimestre → Divulgação → Incremental → Dashboard atualizado
    Q1   →    Maio     →   10 min   →  ✅ Dados Q1 2026
    Q2   →   Agosto    →   10 min   →  ✅ Dados Q2 2026
    Q3   →  Novembro   →   10 min   →  ✅ Dados Q3 2026
    Q4   →    Março    →   10 min   →  ✅ Dados Q4 2026
```

### Consistência

- Mesma lógica do pipeline completo
- Mesmos cálculos e fórmulas
- Apenas processa o necessário

## 🚨 Avisos Importantes

### ⚠️ Não Use Incremental Se:

1. **Mudou mapeamento de tickers** → Use completo
2. **Mudou fórmulas de cálculo** → Use completo
3. **Excel corrompido** → Use completo
4. **Precisa reprocessar histórico** → Use completo

### ⚠️ Limitações

- Não reprocessa trimestres antigos
- Assume que dados históricos estão corretos
- Depende de Excel existente válido

## 🎓 Melhores Práticas

### 1. Rotina Recomendada

```
Mês 1 (após divulgação):
  → Executar incremental
  → Validar novos dados
  → Fazer backup manual (opcional)

Mês 2-3:
  → Usar dashboard normalmente
  → Aguardar próxima divulgação

A cada 1 ano:
  → Executar completo (validação total)
  → Comparar com incremental
```

### 2. Validação Pós-Incremental

Após executar incremental, verifique:

```
✅ Overview → Verificar novo trimestre aparece
✅ Company Analysis → Selecionar empresa → Ver último dado
✅ Resumo_Mercado → Conferir data mais recente
✅ Comparar alguns valores com site da CVM
```

### 3. Troubleshooting

**Problema:** "Nenhum trimestre novo disponível"
- **Causa:** Dados já atualizados
- **Solução:** Aguardar próxima divulgação

**Problema:** "Erro ao processar trimestre X"
- **Causa:** Dados incompletos na CVM
- **Solução:** Tentar novamente dias depois

**Problema:** "Valores estranhos após incremental"
- **Causa:** Possível problema no merge
- **Solução:** Restaurar backup e executar completo

## 🔮 Futuras Melhorias

Planejado para próximas versões:

- [ ] Execução automática agendada (cron)
- [ ] Notificação quando novos dados disponíveis
- [ ] Validação automática pós-incremental
- [ ] Log detalhado de cada execução
- [ ] Comparação antes/depois do incremental
- [ ] Detecção de anomalias nos novos dados

## 📞 Suporte

Se tiver problemas:

1. Verifique logs no terminal
2. Tente executar completo em caso de dúvida
3. Consulte `CLAUDE.md` para detalhes técnicos
4. Restaure backup se necessário

---

**💡 Lembre-se:** Pipeline incremental é para **economizar tempo**, não substituir o completo. Use com sabedoria! 🚀
