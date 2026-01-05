@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo          kRel - Build Script for Windows
echo          Reliability Test Management System
echo ================================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

:: Check/Install PyInstaller
echo [1/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo      Installing PyInstaller...
    pip install pyinstaller
)

:: Clean old build
echo [2/4] Cleaning old build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q *.spec

:: Build executable
echo [3/4] Building executable...
echo      This may take 2-5 minutes...
echo.

pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name "kRel" ^
    --icon "Ka.ico" ^
    --add-data "Ka.ico;." ^
    --add-data "Ka.png;." ^
    --add-data "config.ini;." ^
    --add-data "csv;csv" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "pyodbc" ^
    --hidden-import "pandas" ^
    --hidden-import "openpyxl" ^
    --hidden-import "bcrypt" ^
    --hidden-import "cryptography" ^
    --collect-all "PyQt6" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

:: Copy additional files
echo [4/4] Copying additional files...
if not exist "dist\kRel\Logfile" mkdir "dist\kRel\Logfile"
if not exist "dist\kRel\Logfile\logs" mkdir "dist\kRel\Logfile\logs"

:: Create run script for end users
echo @echo off > "dist\kRel\Run_kRel.bat"
echo cd /d "%%~dp0" >> "dist\kRel\Run_kRel.bat"
echo start "" "kRel.exe" >> "dist\kRel\Run_kRel.bat"

:: Done
echo.
echo ================================================================
echo                     BUILD SUCCESSFUL!
echo ================================================================
echo.
echo   Output folder: dist\kRel\
echo.
echo   To distribute:
echo   1. Copy entire "dist\kRel" folder to target machine
echo   2. Run "kRel.exe" or "Run_kRel.bat"
echo.
echo   Note: Target machine needs:
echo   - Windows 10/11 64-bit
echo   - SQL Server connection (configured in config.ini)
echo   - ODBC Driver 17 for SQL Server
echo ================================================================
echo.

:: Open output folder
explorer "dist\kRel"

pause

