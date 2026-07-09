"use client";

import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const signInWithGoogle = async () => {
    const supabase = createClient();
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-2xl font-semibold">Sign in to chat with uul_chat_ai</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        We ask you to sign in with Google so the owner knows who&apos;s asking.
      </p>
      <button
        onClick={signInWithGoogle}
        className="rounded-md bg-black px-4 py-2 text-white hover:bg-neutral-800"
      >
        Continue with Google
      </button>
    </main>
  );
}
