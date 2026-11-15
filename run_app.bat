@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo پایتون پیدا نشد. اول پایتون رو نصب کن و تیک Add to PATH رو بزن.
    pause
    exit /b 1
)

if not exist venv\Scripts\activate.bat (
    echo در حال ساخت محیط مجازی...
    python -m venv venv
    if errorlevel 1 (
        echo ساخت محیط مجازی ناموفق بود.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

if not exist venv\.installed (
    echo در حال نصب کتابخونه‌ها...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo نصب کتابخونه‌ها ناموفق بود.
        pause
        exit /b 1
    )
    type nul > venv\.installed
)

echo در حال اجرای برنامه...
python run.py

pause