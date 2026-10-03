@echo off
title Dashboard CVM
echo =========================================
echo    Dashboard CVM - Análise Financeira
echo =========================================
echo.

:: Verifica se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado ou nao esta no PATH do Windows.
    echo Por favor, instale o Python 3.11 ou superior: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Verifica se existe base completa ou amostra publica
if exist "pipeline_cvm_final\outputs\base_consolidada.parquet" (
    echo Dados completos encontrados.
) else (
    if exist "data\sample\base_consolidada.parquet" (
        echo Dados completos nao encontrados; usando amostra publica.
    ) else (
        echo [ERRO] Nenhum arquivo Parquet encontrado.
        echo Reinstale o repositorio ou execute: python run_pipeline.py
        pause
        exit /b 1
    )
)

:: Verifica se o streamlit está instalado, se não, instala as dependências
python -m streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias do projeto...
    python -m pip install -r requirements.txt
)

echo.
echo Iniciando o dashboard no seu navegador padrao...
echo Pressione CTRL+C nesta janela quando quiser encerrar o servidor.
echo.

streamlit run app.py
pause
