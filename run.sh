#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 could not be found. Please install Python 3."
    exit 1
fi

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Ask if user wants to load demo data
read -p "Would you like to load demo data? (y/n): " load_demo
if [[ $load_demo == "y" || $load_demo == "Y" ]]; then
    echo "Loading demo data..."
    python demo_data.py
fi

# Run the application
echo "Starting EduRishi Blog..."
streamlit run app.py