"use client";

import { useEffect, useState } from "react";
import { Send } from "lucide-react";
import { getLatestConversation, streamChatMessage } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MessageList, type Message } from "@/components/message-list";

const SUGGESTED_QUESTIONS = [
  "What are your skills?",
  "Tell me about your experience",
  "What projects have you worked on?",
  "How can I contact you?",
];

export function ChatWindow() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [awaitingFirstToken, setAwaitingFirstToken] = useState(false);

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

  const send = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || sending) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    setAwaitingFirstToken(true);

    let assistantAdded = false;
    try {
      for await (const event of streamChatMessage(conversationId, text)) {
        if (event.type === "token") {
          setAwaitingFirstToken(false);
          setMessages((prev) => {
            if (!assistantAdded) {
              assistantAdded = true;
              return [...prev, { role: "assistant", content: event.text }];
            }
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = { role: "assistant", content: last.content + event.text };
            return next;
          });
        } else if (event.type === "done") {
          setConversationId(event.conversation_id);
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setSending(false);
      setAwaitingFirstToken(false);
    }
  };

  return (
    <Card className="w-full max-w-lg overflow-hidden">
      <MessageList
        messages={messages}
        pending={awaitingFirstToken}
        emptyHint="Ask about my skills, experience, or projects — or tap a suggestion below."
        suggestions={SUGGESTED_QUESTIONS}
        onSuggestionClick={(question) => send(question)}
      />
      <CardContent className="flex gap-2 border-t bg-muted/30 p-3">
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && send()}
          placeholder="Ask about my skills, experience, projects…"
          disabled={sending}
        />
        <Button onClick={() => send()} disabled={sending} size="icon" aria-label="Send message">
          <Send className="h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
}
