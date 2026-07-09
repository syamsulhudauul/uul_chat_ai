# uul_chat_ai

Personal AI ops chat portfolio for syamsulhudauul (Applied AI Engineer). Recruiters and clients log in with Google and chat (text or voice) with an AI agent grounded in a curated knowledge base about my skills, experience, and projects.

PRD: https://github.com/syamsulhudauul/uul_chat_ai/issues/1

## Stack

- `fe/` — Next.js 14 + Tailwind + shadcn/ui, Supabase Auth (Google) for login
- `be/` — FastAPI, RAG + tool-calling agent core
- `litellm/` — self-hosted LiteLLM gateway (OpenRouter for chat, OpenAI for STT/TTS/embeddings)
- Supabase — Postgres + pgvector + Auth
- Deploy — Docker Compose on a self-hosted VPS behind Caddy, GitHub Actions CI/CD (build → GHCR → SSH deploy)

## Local development

Backend:

```bash
cd be
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Frontend:

```bash
cd fe
npm install
npm run dev
```

Copy `.env.example` to `.env` and fill in Supabase/OpenRouter/OpenAI credentials.
