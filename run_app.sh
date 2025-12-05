#!/bin/bash

# Launch script for Pennysia Backtest Web Interface

echo "🚀 Starting Pennysia Backtest Web Interface..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    
    # Try python3 first, then python
    if command -v python3 &> /dev/null; then
        python3 -m venv venv
    elif command -v python &> /dev/null; then
        python -m venv venv
    else
        echo "❌ Python not found! Please install Python 3.7 or higher."
        exit 1
    fi
    
    echo "✅ Virtual environment created!"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📥 Checking dependencies..."
if ! python -c "import streamlit" &> /dev/null; then
    echo "📦 Installing dependencies (this may take a minute)..."
    pip install -q --upgrade pip
    pip install -q streamlit plotly requests pandas numpy
    echo "✅ Dependencies installed!"
else
    echo "✅ Dependencies already installed"
fi

# Launch Streamlit app
echo ""
echo "✅ Launching web interface..."
echo "🌐 Your browser will open automatically"
echo "📍 If not, open: http://localhost:8501"
echo ""
echo "💡 Tips:"
echo "   - Use the sidebar to configure settings"
echo "   - You can use the default API key or enter your own"
echo "   - Press Ctrl+C to stop the server"
echo ""

streamlit run app.py
