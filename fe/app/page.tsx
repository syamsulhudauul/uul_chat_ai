import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="flex flex-col gap-3">
        <h1 className="text-4xl font-semibold tracking-tight">uul_chat_ai</h1>
        <p className="max-w-md text-muted-foreground">
          Ask me anything about syamsulhudauul&apos;s skills, experience, and projects — before
          you set up an interview.
        </p>
      </div>
      <Link href="/chat" className={buttonVariants({ size: "lg" })}>
        Start chatting
      </Link>
    </main>
  );
}
