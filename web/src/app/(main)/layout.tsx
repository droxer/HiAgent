"use client";

import { AppSidebar } from "./_components/AppSidebar";
import { CommandPalette } from "@/shared/components";
import { useAppStore } from "@/shared/stores";
import { createConversation } from "@/features/conversation/api/conversation-api";
import { useRouter } from "next/navigation";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { startConversation, resetConversation } = useAppStore();

  const handleNewTask = async (prompt: string) => {
    try {
      const data = await createConversation(prompt);
      startConversation(data.conversation_id, prompt);
      router.push("/");
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  };

  const handleNavigateHome = () => {
    resetConversation();
    router.push("/");
  };

  return (
    <div className="flex h-screen w-screen bg-background">
      <AppSidebar />
      <main className="flex-1 overflow-hidden">{children}</main>
      <CommandPalette
        onNewTask={handleNewTask}
        onNavigateHome={handleNavigateHome}
      />
    </div>
  );
}
