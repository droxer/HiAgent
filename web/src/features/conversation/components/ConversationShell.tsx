"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useSSE } from "@/shared/hooks/use-sse";
import { useAgentState } from "@/features/agent-activity/hooks/use-agent-state";
import { useConversation } from "@/features/conversation/hooks/use-conversation";
import { usePendingAsk } from "@/features/conversation/hooks/use-pending-ask";
import { Sidebar } from "@/shared/components/Sidebar";
import { WelcomeScreen } from "@/features/welcome/components/WelcomeScreen";
import { TaskView } from "@/features/task-view/components/TaskView";
import { InputPrompt } from "@/features/conversation/components/InputPrompt";
import { useAppStore } from "@/features/conversation/stores/conversation-store";

export function ConversationShell() {
  const conversationId = useAppStore((s) => s.conversationId);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);

  const { events, isConnected } = useSSE(conversationId);
  const {
    messages: assistantMessages,
    toolCalls,
    taskState,
    agentStatuses,
    currentIteration,
    reasoningSteps,
    thinkingContent,
  } = useAgentState(events);

  const {
    conversationHistory,
    sidebarCollapsed,
    allMessages,
    handleSendMessage,
    handleCreateConversation,
    handleNewConversation,
  } = useConversation(assistantMessages, taskState);

  const { pendingAsk, handlePromptSubmit, respondError } = usePendingAsk(
    events,
    conversationId,
  );

  const isActive = conversationId !== null;

  return (
    <div className="flex h-screen w-screen bg-background">
      <Sidebar
        taskHistory={conversationHistory}
        onNewTask={handleNewConversation}
        collapsed={sidebarCollapsed}
        onToggle={toggleSidebar}
      />

      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {!isActive ? (
            <motion.div
              key="welcome"
              className="h-full"
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.25 }}
            >
              <WelcomeScreen onSubmitTask={handleCreateConversation} />
            </motion.div>
          ) : (
            <motion.div
              key="taskview"
              className="h-full"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <TaskView
                events={events}
                messages={allMessages}
                toolCalls={toolCalls}
                agentStatuses={agentStatuses}
                taskState={taskState}
                thinkingContent={thinkingContent}
                reasoningSteps={reasoningSteps}
                currentIteration={currentIteration}
                isConnected={isConnected}
                onSendMessage={handleSendMessage}
                onNavigateHome={handleNewConversation}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {pendingAsk && (
        <div>
          <InputPrompt
            question={pendingAsk.question}
            onSubmit={handlePromptSubmit}
          />
          {respondError && (
            <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 rounded-md bg-destructive/90 px-4 py-2 text-sm text-destructive-foreground shadow-lg">
              {respondError}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
