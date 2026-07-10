# Projects

## uul_chat_ai — this project

An AI ops chat portfolio: recruiters and clients log in with Google and chat (text or voice) with an AI agent grounded in this knowledge base. Built with Next.js, FastAPI, a self-hosted LiteLLM gateway (OpenRouter for chat, Voyage AI for embeddings, Gemini for STT/TTS), and Supabase (Postgres + pgvector + Auth). Deployed via Docker Compose across two hosts: a VPS for the app itself and a home server for the LLM gateway, behind Caddy with automatic HTTPS via Cloudflare DNS.

## AI Shopping Assistant — ASTRO

The core applied-AI work of the current role (see Experience for full detail): a production conversational-commerce agent handling real shopping queries — recommendations, recipes, nutrition, budget-aware search. Multi-turn ReAct-style tool-calling loop, LLM-agnostic multi-provider routing, hybrid search/RAG for knowledge grounding, and a full evaluation/guardrail pipeline treating agent behavior as testable software rather than ad-hoc prompt tuning.

## hft_rtb

A Rust-based ultra-low-latency processing stack capable of ingesting market/auction data, applying decision logic, and issuing orders/bids within single-digit-millisecond budgets. Systems-level performance engineering — a different discipline from LLM agent work, but the same underlying instinct for measurable, production-grade software.

## dms (Dynamic MCP Server)

A dynamic Model Context Protocol (MCP) server implementation in Go — infrastructure for exposing tools/capabilities to LLM agents in a standardized, discoverable way. Directly relevant to the tool-calling agent architecture work at ASTRO.
