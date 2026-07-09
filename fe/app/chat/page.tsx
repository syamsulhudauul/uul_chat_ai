import { createClient } from "@/lib/supabase/server";

export default async function ChatPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-xl font-semibold">Chat</h1>
      <p className="text-sm text-muted-foreground">Signed in as {user?.email}</p>
      <p className="text-sm text-muted-foreground">Chat UI lands in #4.</p>
    </main>
  );
}
