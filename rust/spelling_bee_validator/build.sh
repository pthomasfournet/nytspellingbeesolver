#!/bin/bash
# Build script for Rust InputValidator module

set -e  # Exit on error

echo "🦀 Building Spelling Bee Validator (Rust)"
echo "=========================================="

# Check if Rust is installed
if ! command -v rustc &> /dev/null; then
    echo "❌ Error: Rust is not installed"
    echo "   Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo "✅ Rust version: $(rustc --version)"

# Check if maturin is installed
if ! command -v maturin &> /dev/null; then
    echo "⚠️  Maturin not found. Installing..."
    pip install maturin
fi

echo "✅ Maturin version: $(maturin --version)"

# Run tests first
echo ""
echo "🧪 Running Rust unit tests..."
cargo test

if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi

echo "✅ All tests passed!"

# Build the module
echo ""
echo "🔨 Building module in release mode..."
maturin develop --release

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Module installed and ready to use:"
echo "   from spelling_bee_validator import InputValidator"
echo ""
echo "🧪 Run integration tests:"
echo "   pytest python_tests/test_integration.py -v"
echo ""
echo "📊 Run benchmarks:"
echo "   python python_tests/benchmark.py"
echo ""
