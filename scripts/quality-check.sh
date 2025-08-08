#!/bin/bash
# Complete code quality check script

echo "🚀 Running complete code quality checks..."
echo

# Import sorting check
echo "1️⃣ Checking import sorting..."
uv run isort . --diff --check-only
ISORT_EXIT=$?

# Code formatting check  
echo
echo "2️⃣ Checking code formatting..."
uv run black . --diff --check
BLACK_EXIT=$?

# Linting check
echo
echo "3️⃣ Running linting..."
uv run flake8 . --statistics --count
FLAKE8_EXIT=$?

echo
echo "📊 Quality Check Summary:"
echo "========================="

if [ $ISORT_EXIT -eq 0 ]; then
    echo "✅ Import sorting: PASSED"
else
    echo "❌ Import sorting: FAILED"
fi

if [ $BLACK_EXIT -eq 0 ]; then
    echo "✅ Code formatting: PASSED"
else
    echo "❌ Code formatting: FAILED"
fi

if [ $FLAKE8_EXIT -eq 0 ]; then
    echo "✅ Linting: PASSED"
else
    echo "❌ Linting: FAILED"
fi

# Overall result
if [ $ISORT_EXIT -eq 0 ] && [ $BLACK_EXIT -eq 0 ] && [ $FLAKE8_EXIT -eq 0 ]; then
    echo
    echo "🎉 All quality checks passed!"
    exit 0
else
    echo
    echo "💡 Run './scripts/format-fix.sh' to auto-fix formatting issues"
    echo "🔧 Then address any remaining linting issues manually"
    exit 1
fi