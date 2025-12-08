@echo off
echo ========================================
echo Pennysia Backtest - Starting App
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if coins cache exists
if not exist "src\data\coins_cache.py" (
    echo WARNING: Coins cache not found!
    echo You need to build it first:
    echo   python scripts\build_coins_cache.py --api-key YOUR_API_KEY
    echo.
    echo Press any key to continue anyway, or Ctrl+C to cancel...
    pause
)

REM Run the app
echo Starting Streamlit app...
echo.
streamlit run app.py
