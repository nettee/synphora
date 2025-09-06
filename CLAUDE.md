# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- `pnpm dev` - Start development server with Turbopack
- `pnpm build` - Build production application with Turbopack
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

### Package Manager
This project uses `pnpm` as the package manager.

## Architecture

### Project Structure
Synphora is a Next.js 15 application built with React 19 and TypeScript, featuring a chat interface powered by AI models.

**Core Components:**
- `/app` - Next.js App Router structure
  - `/api/chat/route.ts` - Chat API endpoint using AI SDK
  - `page.tsx` - Main chat interface component
  - `layout.tsx` - Root layout with Geist fonts
- `/components` - Component library
  - `/ai-elements` - Custom AI-focused components (conversation, messages, prompt input, etc.)
  - `/ui` - Shadcn/ui components (Radix UI-based)

### Technology Stack
- **Framework:** Next.js 15 with App Router and Turbopack
- **UI Library:** Shadcn/ui (New York style) with Radix UI primitives
- **Styling:** Tailwind CSS v4 with stone base color
- **AI Integration:** Vercel AI SDK (@ai-sdk/react, ai package)
- **Icons:** Lucide React
- **State Management:** React hooks with useChat from AI SDK

### AI Integration
- Chat API supports multiple models (GPT-4o, Deepseek R1)
- Web search capability via Perplexity Sonar
- Streaming responses with source citations and reasoning
- Message parts support text, reasoning, and source-url types

### Styling System
- Uses Tailwind CSS v4 with custom configuration
- Shadcn/ui components with CSS variables for theming
- Custom AI-elements components for chat interface
- Path aliases configured: `@/*` maps to root directory

### Key Features
- Real-time streaming chat interface
- Model selection (GPT-4o, Deepseek R1)
- Web search integration toggle
- Source citations display
- Reasoning step visualization
- Message actions (retry, copy)
- Responsive design with scroll management