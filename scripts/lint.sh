#!/bin/bash
# Code linting script using flake8

echo "🔍 Running code linting with flake8..."
uv run flake8 . --statistics --count

if [ $? -eq 0 ]; then
    echo "✅ No linting issues found!"
else
    echo "❌ Linting issues found. Please fix them before committing."
    exit 1
fi