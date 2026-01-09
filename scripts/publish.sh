#!/bin/bash
# 发布脚本

set -e

echo "🧹 清理旧的构建文件..."
rm -rf dist/ build/ *.egg-info

echo "📦 构建分发包..."
python -m build

echo "✅ 检查分发包..."
twine check dist/*

echo "📤 准备发布..."
echo "要发布到 TestPyPI，运行:"
echo "  twine upload --repository testpypi dist/*"
echo ""
echo "要发布到 PyPI，运行:"
echo "  twine upload dist/*"
