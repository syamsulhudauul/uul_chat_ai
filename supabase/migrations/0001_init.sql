-- uul_chat_ai initial schema
-- users table is managed by Supabase Auth (auth.users) — not created here.

create extension if not exists vector;

create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    mode text not null check (mode in ('chat', 'voice')),
    created_at timestamptz not null default now()
);

create index if not exists conversations_user_id_idx on public.conversations (user_id);

create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations (id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    model_used text,
    created_at timestamptz not null default now()
);

create index if not exists messages_conversation_id_idx on public.messages (conversation_id);

create table if not exists public.knowledge_chunks (
    id uuid primary key default gen_random_uuid(),
    content text not null,
    embedding vector(1024) not null, -- voyage-3 default output dimension
    source_doc text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists knowledge_chunks_source_doc_idx on public.knowledge_chunks (source_doc);

create index if not exists knowledge_chunks_embedding_idx
    on public.knowledge_chunks using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

alter table public.conversations enable row level security;
alter table public.messages enable row level security;

create policy "users manage their own conversations"
    on public.conversations
    for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "users manage their own messages"
    on public.messages
    for all
    using (
        exists (
            select 1 from public.conversations c
            where c.id = conversation_id and c.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1 from public.conversations c
            where c.id = conversation_id and c.user_id = auth.uid()
        )
    );

-- knowledge_chunks has no RLS: it's global content the BE service role manages,
-- read via the BE's RAG Retriever (service role), not directly from the FE.
