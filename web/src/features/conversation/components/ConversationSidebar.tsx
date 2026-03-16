"use client";

import { useEffect, useRef } from "react";
import { Sidebar } from "@/shared/components";
import { useAppStore } from "@/shared/stores";
import { useConversationContext } from "../hooks/use-conversation-context";

export function ConversationSidebar() {
  const { conversationId, handleSwitchConversation, handleNewConversation } =
    useConversationContext();
  const {
    conversationHistory,
    sidebarCollapsed,
    sidebarWidth,
    toggleSidebar,
    setSidebarWidth,
    loadConversations,
    loadMore,
    searchQuery,
    setSearchQuery,
    deleteConversation,
  } = useAppStore();

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Debounced search: reload conversations 300ms after searchQuery changes
  const isFirstRender = useRef(true);
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    const timer = setTimeout(() => {
      loadConversations();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, loadConversations]);

  return (
    <Sidebar
      taskHistory={conversationHistory}
      activeTaskId={conversationId}
      onNewTask={handleNewConversation}
      onSelectTask={handleSwitchConversation}
      collapsed={sidebarCollapsed}
      width={sidebarWidth}
      onToggle={toggleSidebar}
      onWidthChange={setSidebarWidth}
      onLoadMore={loadMore}
      searchQuery={searchQuery}
      onSearchChange={setSearchQuery}
      onDeleteTask={deleteConversation}
    />
  );
}
