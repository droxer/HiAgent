"use client";

import { ConversationProvider } from "./ConversationProvider";
import { ConversationView } from "./ConversationView";
import { PendingAskOverlay } from "./PendingAskOverlay";

export function ConversationShell() {
  return (
    <ConversationProvider>
      <ConversationView />
      <PendingAskOverlay />
    </ConversationProvider>
  );
}
