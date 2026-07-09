import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "uul_chat_ai",
  description: "Chat with an AI about syamsulhudauul's skills, experience, and projects.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
