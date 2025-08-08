#!/bin/bash
# Code formatting script using Black and isort

echo "🔧 Running import sorting with isort..."
uv run isort . --diff --check-only

echo "🎨 Running code formatting with Black..."
uv run black . --diff --check

echo "✅ Format check completed!"