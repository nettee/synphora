# VS Code 配置说明

## 🚀 快速开始

### 1. 安装推荐扩展

VS Code 会自动提示安装推荐的扩展，或者你可以手动安装：

**必需扩展：**

- `charliermarsh.ruff` - Ruff 扩展（代码格式化和检查）
- `ms-python.python` - Python 扩展
- `ms-python.vscode-pylance` - Python 语言服务器

### 2. 确保项目环境正确

```bash
# 切换到后端目录
cd backend/

# 安装依赖（包括 ruff）
uv sync

# 激活虚拟环境（如果需要）
source .venv/bin/activate
```

## 🔧 配置功能

### 自动格式化和修复

以下操作会自动触发：

1. **保存文件时**：

   - 使用 Ruff 格式化代码
   - 自动整理导入语句
   - 自动修复可修复的问题

2. **手动操作**：
   - `Cmd+Shift+P` → "Format Document" - 格式化文档
   - `Cmd+Shift+P` → "Organize Imports" - 整理导入
   - `Cmd+Shift+P` → "Ruff: Fix all auto-fixable problems" - 修复所有问题

### 快捷键

| 操作       | 快捷键 (Mac)  | 快捷键 (Windows/Linux) |
| ---------- | ------------- | ---------------------- |
| 格式化文档 | `Shift+Opt+F` | `Shift+Alt+F`          |
| 快速修复   | `Cmd+.`       | `Ctrl+.`               |

## 📁 文件结构

```
.vscode/
├── settings.json      # 工作区设置
├── extensions.json    # 推荐扩展
└── README.md         # 本说明文件
```

## 🎯 配置详解

### Python 解释器

配置会自动使用项目的虚拟环境：

```json
"python.defaultInterpreterPath": "./backend/.venv/bin/python"
```

### Ruff 配置

- **格式化**：`ruff.format.enable: true`
- **代码检查**：`ruff.lint.enable: true`
- **自动修复**：`ruff.fixAll: true`
- **导入整理**：`ruff.organizeImports: true`

### 文件保存行为

- 保存时自动格式化
- 移除行尾空白字符
- 确保文件末尾有换行符

## 🚫 避免冲突

配置中已排除可能与 Ruff 冲突的扩展：

- `ms-python.flake8`
- `ms-python.pylint`
- `ms-python.black-formatter`

## 🛠️ 故障排除

### Ruff 未生效？

1. 确认已安装 Ruff 扩展
2. 检查 Python 解释器路径是否正确
3. 确保项目中已安装 ruff：`uv run ruff --version`
4. 重启 VS Code

### 格式化不符合预期？

检查 `backend/pyproject.toml` 中的 Ruff 配置，特别是：

```toml
[tool.ruff.format]
quote-style = "preserve"  # 保持原有引号样式
```

### 导入整理问题？

Ruff 的导入整理功能在保存时自动触发，如果需要手动触发：

- `Cmd+Shift+P` → "Organize Imports"
