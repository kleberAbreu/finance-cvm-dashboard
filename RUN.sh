#!/bin/bash

# Script de execução do Dashboard CVM
# Uso: ./RUN.sh

echo "🚀 Dashboard CVM - Iniciando..."
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale Python 3.11+ primeiro."
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"
echo ""

# Verificar Streamlit
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit não encontrado. Instalando dependências..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "✅ Streamlit instalado"
echo ""

# Verificar arquivo Parquet de produção ou amostra
if [ -f "pipeline_cvm_final/outputs/base_consolidada.parquet" ]; then
    echo "✅ Dados completos encontrados"
elif [ -f "data/sample/base_consolidada.parquet" ]; then
    echo "ℹ️  Dados completos não encontrados; usando amostra pública"
else
    echo "❌ Nenhum arquivo Parquet encontrado."
    echo "   Reinstale o repositório ou execute: python3 run_pipeline.py"
    exit 1
fi

echo ""

# Executar dashboard
echo "🎯 Iniciando dashboard..."
echo "   Acesse: http://localhost:8501"
echo ""
echo "   Pressione Ctrl+C para parar"
echo ""

streamlit run app.py
