#!/bin/bash
# Auto-fix formatting issues with Black and isort

echo "🔧 Fixing import sorting with isort..."
uv run isort .

echo "🎨 Fixing code formatting with Black..."
uv run black .

echo "✅ Formatting fixes applied!"