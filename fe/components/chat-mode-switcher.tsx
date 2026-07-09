"use client";

import { useState } from "react";
import { ChatWindow } from "@/components/chat-window";
import { VoiceWindow } from "@/components/voice-window";

type Mode = "chat" | "voice";

export function ChatModeSwitcher() {
  const [mode, setMode] = useState<Mode>("chat");

  return (
    <div className="flex w-full max-w-lg flex-col items-center gap-4">
      <div className="flex gap-1 rounded-full border p-1 text-sm">
        <button
          onClick={() => setMode("chat")}
          className={`rounded-full px-4 py-1 ${mode === "chat" ? "bg-black text-white" : ""}`}
        >
          Chat
        </button>
        <button
          onClick={() => setMode("voice")}
          className={`rounded-full px-4 py-1 ${mode === "voice" ? "bg-black text-white" : ""}`}
        >
          Voice
        </button>
      </div>
      {mode === "chat" ? <ChatWindow /> : <VoiceWindow />}
    </div>
  );
}
