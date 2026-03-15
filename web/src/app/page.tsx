"use client";

import { ConversationShell } from "@/features/conversation/components/ConversationShell";
import { ErrorBoundary } from "@/shared/components/ErrorBoundary";

export default function Page() {
  return (
    <ErrorBoundary>
      <ConversationShell />
    </ErrorBoundary>
  );
}
