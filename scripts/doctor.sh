#!/bin/bash
#
# Environment doctor: Check system requirements and dependencies
#

set -e

echo "🏥 Polymarket Bot - Environment Doctor"
echo "======================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

ERRORS=0
WARNINGS=0

# Check Python
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✅ $PYTHON_VERSION"
    
    # Check if version is 3.8+
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
        echo "  ⚠️  Python 3.8+ recommended (you have $PYTHON_VERSION)"
        ((WARNINGS++))
    fi
else
    echo "  ❌ Python 3 not found"
    echo "     Install: brew install python3 (macOS) or apt install python3 (Ubuntu)"
    ((ERRORS++))
fi

echo ""

# Check pip
echo "📦 Checking pip..."
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    echo "  ✅ pip installed"
else
    echo "  ❌ pip not found"
    echo "     Install: python3 -m ensurepip --upgrade"
    ((ERRORS++))
fi

echo ""

# Check virtual environment
echo "🔧 Checking virtual environment..."
if [ -d "venv" ]; then
    echo "  ✅ Virtual environment exists"
    
    # Activate and check packages
    source venv/bin/activate
    
    echo ""
    echo "📚 Checking installed packages..."
    
    PACKAGES=("playwright" "websockets" "requests" "pandas" "numpy")
    for pkg in "${PACKAGES[@]}"; do
        if pip show "$pkg" &> /dev/null; then
            VERSION=$(pip show "$pkg" | grep Version | cut -d' ' -f2)
            echo "  ✅ $pkg ($VERSION)"
        else
            echo "  ❌ $pkg not installed"
            ((ERRORS++))
        fi
    done
    
    deactivate
else
    echo "  ⚠️  Virtual environment not found"
    echo "     Will be created automatically on first run"
    ((WARNINGS++))
fi

echo ""

# Check Playwright
echo "🌐 Checking Playwright browsers..."
if [ -d "venv" ]; then
    source venv/bin/activate
    
    if command -v playwright &> /dev/null; then
        echo "  ✅ Playwright CLI installed"
        
        # Check if chromium is installed
        if playwright install chromium --dry-run 2>&1 | grep -q "is already installed"; then
            echo "  ✅ Chromium browser installed"
        else
            echo "  ⚠️  Chromium browser not installed"
            echo "     Run: playwright install chromium"
            ((WARNINGS++))
        fi
    else
        echo "  ⚠️  Playwright not installed"
        ((WARNINGS++))
    fi
    
    deactivate
else
    echo "  ⚠️  Cannot check (venv not found)"
    ((WARNINGS++))
fi

echo ""

# Check config files
echo "📋 Checking configuration files..."
if [ -f "config.json" ]; then
    echo "  ✅ config.json exists"
else
    if [ -f "config.json.example" ]; then
        echo "  ⚠️  config.json not found (example exists)"
        echo "     Run: cp config.json.example config.json"
        ((WARNINGS++))
    else
        echo "  ❌ config.json.example not found"
        ((ERRORS++))
    fi
fi

if [ -f "state.json" ]; then
    echo "  ✅ state.json exists"
else
    if [ -f "state.json.example" ]; then
        echo "  ℹ️  state.json not found (will be created automatically)"
    else
        echo "  ❌ state.json.example not found"
        ((ERRORS++))
    fi
fi

echo ""

# Check network connectivity
echo "🌍 Checking network connectivity..."

# Test Gamma API
if curl -s --max-time 5 "https://gamma-api.polymarket.com/markets?limit=1" > /dev/null 2>&1; then
    echo "  ✅ Gamma API reachable"
else
    echo "  ⚠️  Gamma API not reachable"
    echo "     Check your internet connection"
    ((WARNINGS++))
fi

# Test Polymarket
if curl -s --max-time 5 "https://polymarket.com" > /dev/null 2>&1; then
    echo "  ✅ Polymarket reachable"
else
    echo "  ⚠️  Polymarket not reachable"
    echo "     Check your internet connection"
    ((WARNINGS++))
fi

echo ""

# Check logs directory
echo "📁 Checking logs directory..."
if [ -d "logs" ]; then
    echo "  ✅ logs/ directory exists"
else
    echo "  ℹ️  logs/ directory not found (will be created automatically)"
fi

echo ""
echo "======================================"
echo "📊 Summary"
echo "======================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Environment is ready."
    echo ""
    echo "Next steps:"
    echo "  1. Review/edit config.json"
    echo "  2. Run: ./scripts/run_btc.sh or ./scripts/run_eth.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  $WARNINGS warning(s) found - environment should work but some optional features may be unavailable"
    echo ""
    echo "You can try running the bot, it may work or may auto-fix some issues."
    exit 0
else
    echo "❌ $ERRORS error(s) and $WARNINGS warning(s) found"
    echo ""
    echo "Please fix the errors above before running the bot."
    exit 1
fi
