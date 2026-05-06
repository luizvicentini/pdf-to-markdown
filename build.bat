@echo off
REM ============================================================
REM Builda o executável Windows com PyInstaller (modo --onedir).
REM Duplo-clique aqui ou execute pelo cmd. Saída em dist\PDF-to-Markdown\
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo === Verificando Python ===
where python >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    echo Instale Python 3.10+ e marque "Add Python to PATH".
    pause
    exit /b 1
)
python --version

echo.
echo === Verificando dependencias ===
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar requirements.txt
    pause
    exit /b 1
)

python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    python -m pip install --quiet pyinstaller==6.11.1
    if errorlevel 1 (
        echo ERRO: Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo.
echo === Limpando builds anteriores ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo === Empacotando com PyInstaller ===
python -m PyInstaller --noconfirm --clean build.spec
if errorlevel 1 (
    echo.
    echo ERRO: Build falhou. Veja mensagens acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  BUILD CONCLUIDO
echo  Executavel: dist\PDF-to-Markdown\PDF-to-Markdown.exe
echo  De duplo-clique para rodar.
echo ============================================================
pause
endlocal
