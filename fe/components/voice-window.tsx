"use client";

import { useEffect, useRef, useState } from "react";
import { getLatestConversation, sendVoiceMessage } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export function VoiceWindow() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    getLatestConversation("voice")
      .then((res) => {
        setConversationId(res.conversation_id);
        setMessages(res.messages);
      })
      .catch(() => {
        // No prior voice conversation yet, or the BE isn't reachable — start fresh.
      });
  }, []);

  const startRecording = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await sendRecording(blob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch {
      setError("Couldn't access your microphone. Check browser permissions.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const sendRecording = async (blob: Blob) => {
    setProcessing(true);
    try {
      const result = await sendVoiceMessage(conversationId, blob);
      setConversationId(result.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "user", content: result.transcript },
        { role: "assistant", content: result.reply },
      ]);

      const audio = new Audio(`data:audio/mpeg;base64,${result.audio_base64}`);
      void audio.play();
    } catch {
      setError("Something went wrong processing that recording. Please try again.");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="flex w-full max-w-lg flex-col gap-4">
      <div className="flex min-h-[320px] flex-col gap-2 rounded-md border p-4">
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Hold the mic button and ask about my skills, experience, or projects.
          </p>
        )}
        {messages.map((message, index) => (
          <div key={index} className={message.role === "user" ? "text-right" : "text-left"}>
            <span className="inline-block rounded-md bg-neutral-100 px-3 py-2 text-sm text-black">
              {message.content}
            </span>
          </div>
        ))}
        {processing && <p className="text-sm text-muted-foreground">Thinking…</p>}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={recording ? stopRecording : startRecording}
        disabled={processing}
        className={`self-center rounded-full px-6 py-3 text-sm text-white disabled:opacity-50 ${
          recording ? "bg-red-600" : "bg-black"
        }`}
      >
        {recording ? "Stop recording" : processing ? "Processing…" : "Start recording"}
      </button>
    </div>
  );
}
