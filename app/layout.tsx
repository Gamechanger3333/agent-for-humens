import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "FreelanceOps Agent",
  description:
    "An agent that drafts proposals, chases quiet leads, and reminds clients about overdue invoices — built with Strands Agents on Amazon Bedrock.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
