"use client";

import { useEffect, useState } from "react";
import { getLatestConversation, sendChatMessage } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export function ChatWindow() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getLatestConversation()
      .then((res) => {
        setConversationId(res.conversation_id);
        setMessages(res.messages);
      })
      .catch(() => {
        // No prior conversation yet, or the BE isn't reachable — start fresh.
      })
      .finally(() => setLoaded(true));
  }, []);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);

    try {
      const { reply, conversation_id } = await sendChatMessage(conversationId, text);
      setConversationId(conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex w-full max-w-lg flex-col gap-4">
      <div className="flex min-h-[320px] flex-col gap-2 rounded-md border p-4">
        {loaded && messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Ask about my skills, experience, or projects.
          </p>
        )}
        {messages.map((message, index) => (
          <div key={index} className={message.role === "user" ? "text-right" : "text-left"}>
            <span className="inline-block rounded-md bg-neutral-100 px-3 py-2 text-sm text-black">
              {message.content}
            </span>
          </div>
        ))}
        {sending && <p className="text-sm text-muted-foreground">Thinking…</p>}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-md border px-3 py-2 text-sm"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && send()}
          placeholder="Ask about my skills, experience, projects…"
        />
        <button
          onClick={send}
          disabled={sending}
          className="rounded-md bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
