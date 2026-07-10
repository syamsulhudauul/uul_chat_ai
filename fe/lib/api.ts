import { createClient } from "@/lib/supabase/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ChatStreamEvent =
  | { type: "token"; text: string }
  | { type: "done"; model_used: string; text: string; conversation_id: string };

export type ConversationHistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type LatestConversationResponse = {
  conversation_id: string | null;
  messages: ConversationHistoryMessage[];
};

async function authHeader(): Promise<Record<string, string>> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
}

export async function* streamChatMessage(
  conversationId: string | null,
  message: string
): AsyncGenerator<ChatStreamEvent> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeader()),
    },
    body: JSON.stringify({ conversation_id: conversationId, message }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? ""; // last chunk may be incomplete — keep it buffered

    for (const rawEvent of events) {
      const line = rawEvent.trim();
      if (!line.startsWith("data: ")) continue;
      yield JSON.parse(line.slice("data: ".length)) as ChatStreamEvent;
    }
  }
}

export async function getLatestConversation(
  mode: "chat" | "voice" = "chat"
): Promise<LatestConversationResponse> {
  const response = await fetch(`${API_BASE_URL}/conversations/latest?mode=${mode}`, {
    headers: await authHeader(),
  });

  if (!response.ok) {
    throw new Error(`Failed to load conversation with status ${response.status}`);
  }

  return response.json();
}

export type VoiceResponse = {
  conversation_id: string;
  transcript: string;
  reply: string;
  model_used: string;
  audio_base64: string;
};

export async function sendVoiceMessage(
  conversationId: string | null,
  audio: Blob
): Promise<VoiceResponse> {
  const formData = new FormData();
  formData.append("file", audio, "recording.webm");
  if (conversationId) {
    formData.append("conversation_id", conversationId);
  }

  const response = await fetch(`${API_BASE_URL}/voice`, {
    method: "POST",
    headers: await authHeader(),
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Voice request failed with status ${response.status}`);
  }

  return response.json();
}
