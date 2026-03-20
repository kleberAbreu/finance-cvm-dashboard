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
    echo Por favor, instale o Python 3.8 ou superior: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Verifica se o arquivo parquet principal existe (o novo padrão parquet)
if not exist "pipeline_cvm_final\outputs\base_consolidada.parquet" (
    echo [ERRO] Arquivo de dados Parquet nao encontrado!
    echo Execute o pipeline de processamento primeiro para gerar os dados.
    pause
    exit /b 1
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
