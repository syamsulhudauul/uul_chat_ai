"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, Square } from "lucide-react";
import { getLatestConversation, sendVoiceMessage } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { MessageList, type Message } from "@/components/message-list";

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
    <Card className="w-full max-w-lg overflow-hidden">
      <MessageList
        messages={messages}
        pending={processing}
        emptyHint="Hold the mic button and ask about my skills, experience, or projects."
      />
      <CardContent className="flex flex-col items-center gap-2 border-t bg-muted/30 p-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button
          onClick={recording ? stopRecording : startRecording}
          disabled={processing}
          size="icon"
          variant={recording ? "destructive" : "default"}
          aria-label={recording ? "Stop recording" : "Start recording"}
          className={cn("h-14 w-14", recording && "animate-pulse")}
        >
          {recording ? <Square className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
        </Button>
        <p className="text-xs text-muted-foreground">
          {recording ? "Recording — tap to stop" : processing ? "Processing…" : "Tap to talk"}
        </p>
      </CardContent>
    </Card>
  );
}
