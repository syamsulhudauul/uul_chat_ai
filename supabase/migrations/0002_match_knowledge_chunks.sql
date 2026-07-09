-- RPC used by RAGRetriever via PostgREST (/rest/v1/rpc/match_knowledge_chunks).
create or replace function match_knowledge_chunks(
    query_embedding vector(1536),
    match_count int default 5
)
returns table (
    id uuid,
    content text,
    source_doc text,
    metadata jsonb,
    similarity float
)
language sql stable
as $$
    select
        id,
        content,
        source_doc,
        metadata,
        1 - (embedding <=> query_embedding) as similarity
    from knowledge_chunks
    order by embedding <=> query_embedding
    limit match_count;
$$;
