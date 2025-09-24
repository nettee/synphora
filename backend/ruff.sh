#!/bin/bash
# Ruff 工具脚本

case "$1" in
    "check")
        echo "🔍 检查代码质量..."
        uv run ruff check src/
        ;;
    "fix")
        echo "🔧 自动修复问题..."
        uv run ruff check --fix src/
        ;;
    "format")
        echo "🎨 格式化代码..."
        uv run ruff format src/
        ;;
    "all")
        echo "🎨 格式化代码..."
        uv run ruff format src/
        echo "🔧 自动修复问题..."
        uv run ruff check --fix src/
        echo "🔍 最终检查..."
        uv run ruff check src/
        ;;
    *)
        echo "Ruff 工具使用说明："
        echo "  ./ruff.sh check   - 检查代码质量"
        echo "  ./ruff.sh fix     - 自动修复问题"
        echo "  ./ruff.sh format  - 格式化代码"
        echo "  ./ruff.sh all     - 执行所有操作"
        ;;
esac
