"use client";

import { useEffect, useRef } from "react";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

export type Message = { role: "user" | "assistant"; content: string };

export function MessageList({
  messages,
  pending = false,
  emptyHint,
  suggestions,
  onSuggestionClick,
}: {
  messages: Message[];
  pending?: boolean;
  emptyHint: string;
  suggestions?: string[];
  onSuggestionClick?: (question: string) => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, pending]);

  return (
    <div className="flex h-80 flex-col gap-3 overflow-y-auto p-4">
      {messages.length === 0 && !pending && (
        <div className="m-auto flex max-w-xs flex-col items-center gap-3 text-center">
          <p className="text-sm text-muted-foreground">{emptyHint}</p>
          {suggestions && suggestions.length > 0 && (
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((question) => (
                <button
                  key={question}
                  onClick={() => onSuggestionClick?.(question)}
                  className="rounded-full border bg-background px-3 py-1.5 text-xs text-foreground transition-colors hover:bg-muted"
                >
                  {question}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {messages.map((message, index) => (
        <div
          key={index}
          className={cn(
            "flex items-end gap-2",
            message.role === "user" ? "flex-row-reverse" : "flex-row"
          )}
        >
          <span
            className={cn(
              "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
              message.role === "user"
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            )}
          >
            {message.role === "user" ? (
              <User className="h-4 w-4" />
            ) : (
              <Bot className="h-4 w-4" />
            )}
          </span>
          <span
            className={cn(
              "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm",
              message.role === "user"
                ? "rounded-br-sm bg-primary text-primary-foreground"
                : "rounded-bl-sm bg-muted text-foreground"
            )}
          >
            {message.content}
          </span>
        </div>
      ))}

      {pending && (
        <div className="flex items-end gap-2">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Bot className="h-4 w-4" />
          </span>
          <span className="flex items-center gap-1 rounded-2xl rounded-bl-sm bg-muted px-4 py-3">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" />
          </span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
