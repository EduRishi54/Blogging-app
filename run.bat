@echo off
echo Setting up EduRishi Blog...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python could not be found. Please install Python 3.
    exit /b 1
)

:: Check if virtual environment exists, if not create one
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt

:: Ask if user wants to load demo data
set /p load_demo="Would you like to load demo data? (y/n): "
if /i "%load_demo%"=="y" (
    echo Loading demo data...
    python demo_data.py
)

:: Run the application
echo Starting EduRishi Blog...
streamlit run app.py

pause