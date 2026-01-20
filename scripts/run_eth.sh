#!/bin/bash
#
# Run ETH trading bot
#

set -e

echo "🚀 Polymarket One-Click Bot - ETH"
echo "=================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Install Playwright browsers if needed
if ! playwright --version &> /dev/null; then
    echo "🌐 Installing Playwright browsers..."
    playwright install chromium
else
    echo "✅ Playwright already installed"
fi

# Run bot
echo ""
echo "🎯 Starting ETH bot..."
echo ""

python -m src.main --asset eth "$@"

# Deactivate venv
deactivate

echo ""
echo "✅ Bot stopped"
