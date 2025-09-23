# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Frontend Development (in `/frontend` directory)

Package Manager: `pnpm`

- `pnpm dev` - Start development server with Turbopack

### Backend Development (in `/backend` directory)

Package Manager: `uv`

- `uv run dev` - Start backend server with auto-reload
- `curl -X GET "http://127.0.0.1:8000/health"` - Health check endpoint
- `curl -X POST "http://127.0.0.1:8000/agent" -H "Content-Type: application/json" -d '{"message": "Hello"}'` - Send chat request

## Architecture

### Project Structure
Synphora is a full-stack application with a Next.js frontend and FastAPI backend, featuring a chat interface powered by AI models.

**Frontend (`/frontend`):**
- `/app` - Next.js App Router structure
  - `/api/chat/route.ts` - Chat API endpoint using AI SDK
  - `page.tsx` - Main chat interface component
  - `layout.tsx` - Root layout with Geist fonts
- `/components` - Component library
  - `/ai-elements` - Custom AI-focused components (conversation, messages, prompt input, etc.)
  - `/ui` - Shadcn/ui components (Radix UI-based)

**Backend (`/backend`):**
- `/src/synphora` - Python backend source
  - `server.py` - FastAPI server with SSE endpoints
  - `agent.py` - AI agent implementation
  - `llm.py` - Language model integration
  - `sse.py` - Server-sent events utilities
- `pyproject.toml` - Python project configuration

### Technology Stack

**Frontend:**
- **Framework:** Next.js 15 with App Router and Turbopack
- **UI Library:** Shadcn/ui (New York style) with Radix UI primitives
- **Styling:** Tailwind CSS v4 with stone base color
- **AI Integration:** Vercel AI SDK (@ai-sdk/react, ai package)
- **Icons:** Lucide React
- **State Management:** React hooks with useChat from AI SDK

**Backend:**
- **Framework:** FastAPI with Python 3.13+
- **Package Manager:** uv for dependency management
- **AI Integration:** LangChain Core, LangChain OpenAI, LangGraph
- **Server:** Uvicorn ASGI server
- **Communication:** Server-Sent Events (SSE) for real-time streaming

### AI Integration
- Backend provides HTTP SSE endpoints for AI agent communication
- Support for multiple models (OpenAI GPT-4o, etc.)
- Web search capability integration
- Streaming responses with real-time communication
- LangChain-based agent architecture with LangGraph

### Communication Flow
- Frontend communicates with backend via HTTP SSE
- Backend `/agent` endpoint accepts POST requests with text, model, and webSearch parameters
- Real-time streaming responses from backend to frontend
- Health check endpoint at `/health`

### Key Features
- Full-stack AI chat application
- Real-time streaming chat interface via SSE
- Model selection and web search integration
- Modular frontend components for AI interactions
- Scalable backend architecture with FastAPI
- Development-friendly with hot reload on both frontend and backend