"use client";

import { useState } from "react";
import { MessageSquare, Mic } from "lucide-react";
import { ChatWindow } from "@/components/chat-window";
import { VoiceWindow } from "@/components/voice-window";
import { cn } from "@/lib/utils";

type Mode = "chat" | "voice";

export function ChatModeSwitcher() {
  const [mode, setMode] = useState<Mode>("chat");

  return (
    <div className="flex w-full max-w-lg flex-col items-center gap-4">
      <div className="flex gap-1 rounded-full border bg-card p-1 text-sm shadow-sm">
        <button
          onClick={() => setMode("chat")}
          className={cn(
            "flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors",
            mode === "chat"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <MessageSquare className="h-3.5 w-3.5" />
          Chat
        </button>
        <button
          onClick={() => setMode("voice")}
          className={cn(
            "flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors",
            mode === "voice"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Mic className="h-3.5 w-3.5" />
          Voice
        </button>
      </div>
      {mode === "chat" ? <ChatWindow /> : <VoiceWindow />}
    </div>
  );
}
