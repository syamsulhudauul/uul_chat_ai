import { createClient } from "@/lib/supabase/server";
import { ChatModeSwitcher } from "@/components/chat-mode-switcher";

export default async function ChatPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-xl font-semibold">Chat with uul_chat_ai</h1>
      <p className="text-sm text-muted-foreground">Signed in as {user?.email}</p>
      <ChatModeSwitcher />
    </main>
  );
}
