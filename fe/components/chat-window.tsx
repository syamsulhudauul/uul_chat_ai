"use client";

import { useEffect, useState } from "react";
import { Send } from "lucide-react";
import { getLatestConversation, sendChatMessage } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MessageList, type Message } from "@/components/message-list";

export function ChatWindow() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    getLatestConversation("chat")
      .then((res) => {
        setConversationId(res.conversation_id);
        setMessages(res.messages);
      })
      .catch(() => {
        // No prior conversation yet, or the BE isn't reachable — start fresh.
      });
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
    <Card className="w-full max-w-lg overflow-hidden">
      <MessageList
        messages={messages}
        pending={sending}
        emptyHint="Ask about my skills, experience, or projects."
      />
      <CardContent className="flex gap-2 border-t bg-muted/30 p-3">
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && send()}
          placeholder="Ask about my skills, experience, projects…"
          disabled={sending}
        />
        <Button onClick={send} disabled={sending} size="icon" aria-label="Send message">
          <Send className="h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
}
