#!/bin/bash

echo "🚀 Starting MeriNetWorth Dashboard..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync dependencies with uv
echo "📥 Syncing dependencies with uv..."
uv sync --quiet

# Check if data exists
if [ ! -f "output/bank_data.json" ]; then
    echo ""
    echo "⚠️  No processed data found!"
    echo "📊 Please run the data processor first:"
    echo "   python process_all.py"
    echo ""
    read -rp "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Launch dashboard
echo ""
echo "🌐 Launching dashboard at http://localhost:8501"
echo "   (Press Ctrl+C to stop)"
echo ""

uv run streamlit run web/app.py
