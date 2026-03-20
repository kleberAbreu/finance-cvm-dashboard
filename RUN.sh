#!/bin/bash

# Script de execução do Dashboard CVM
# Uso: ./RUN.sh

echo "🚀 Dashboard CVM - Iniciando..."
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale Python 3.8+ primeiro."
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

# Verificar arquivo Parquet
if [ ! -f "pipeline_cvm_final/outputs/base_consolidada.parquet" ]; then
    echo "❌ Arquivo Parquet não encontrado!"
    echo "   Caminho esperado: pipeline_cvm_final/outputs/base_consolidada.parquet"
    echo ""
    echo "   Execute o pipeline de processamento primeiro para gerar os dados."
    exit 1
fi

echo "✅ Arquivo de dados Parquet encontrado"
echo ""

# Executar dashboard
echo "🎯 Iniciando dashboard..."
echo "   Acesse: http://localhost:8501"
echo ""
echo "   Pressione Ctrl+C para parar"
echo ""

streamlit run app.py
