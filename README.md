# Synphora

一个基于 Next.js 15 构建的现代化 AI 聊天应用，支持多种 AI 模型和网络搜索功能。

## ✨ 特性

- 🤖 **多模型支持** - 支持 GPT-4o 和 Deepseek R1 等多种 AI 模型
- 🌐 **网络搜索** - 集成 Perplexity Sonar 进行实时网络搜索
- 💬 **流式对话** - 实时流式响应，提供流畅的对话体验
- 📚 **引用来源** - 显示回答的引用来源和推理过程
- 🎨 **现代化 UI** - 基于 Shadcn/ui 和 Tailwind CSS 的精美界面
- ⚡ **高性能** - 使用 Turbopack 加速开发和构建

## 🚀 快速开始

### 环境要求

- Node.js 18+
- pnpm

### 安装依赖

```bash
pnpm install
```

### 开发环境

```bash
pnpm dev
```

### 生产构建

```bash
pnpm build
pnpm start
```

## 🛠️ 技术栈

- **框架**: Next.js 15 (App Router)
- **前端**: React 19 + TypeScript
- **样式**: Tailwind CSS v4 + Shadcn/ui
- **AI 集成**: Vercel AI SDK
- **构建工具**: Turbopack
- **包管理**: pnpm

## 📁 项目结构

```
synphora/
├── app/                    # Next.js App Router
│   ├── api/chat/          # 聊天 API 端点
│   ├── layout.tsx         # 根布局
│   └── page.tsx           # 主页面
├── components/            # 组件库
│   ├── ai-elements/       # AI 相关组件
│   └── ui/               # 基础 UI 组件
├── lib/                   # 工具函数
└── public/               # 静态资源
```

## 🔧 可用脚本

- `pnpm dev` - 启动开发服务器
- `pnpm build` - 构建生产版本
- `pnpm start` - 启动生产服务器
- `pnpm lint` - 运行代码检查

## 🎯 核心功能

### AI 模型切换
应用支持在 GPT-4o 和 Deepseek R1 之间切换，满足不同的对话需求。

### 网络搜索
开启搜索功能后，AI 可以访问最新的网络信息来回答问题。

### 流式响应
采用流式传输技术，让用户能够实时看到 AI 的回复过程。

### 引用来源
对于基于网络搜索的回答，系统会显示相关的引用来源。

### 推理过程
部分模型支持显示推理步骤，让用户了解 AI 的思考过程。

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。