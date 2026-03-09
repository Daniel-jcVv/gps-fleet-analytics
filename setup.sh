#!/usr/bin/env bash
set -e

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt -q

if [ ! -f .env ]; then
    read -p "Enter your Groq API key (or press Enter to skip): " groq_key
    if [ -n "$groq_key" ]; then
        echo "GROQ_API_KEY=$groq_key" > .env
        echo "Created .env"
    else
        echo "Skipped .env — AI chat will not work without it"
    fi
fi

echo "Running ETL pipeline..."
python main.py

echo "Done. Launch the dashboard with:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py"
