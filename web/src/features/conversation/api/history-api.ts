import { API_BASE } from "@/shared/constants";

export interface ConversationListItem {
  readonly id: string;
  readonly title: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface ConversationListResponse {
  readonly items: readonly ConversationListItem[];
  readonly total: number;
}

export interface HistoryMessage {
  readonly id: string;
  readonly role: "user" | "assistant" | "tool";
  readonly content: Record<string, unknown>;
  readonly iteration: number | null;
  readonly created_at: string;
}

export interface ConversationMessagesResponse {
  readonly conversation_id: string;
  readonly title: string | null;
  readonly messages: readonly HistoryMessage[];
}

export async function fetchConversations(
  limit = 20,
  offset = 0,
  search?: string,
): Promise<ConversationListResponse> {
  let url = `${API_BASE}/conversations?limit=${limit}&offset=${offset}`;
  if (search) {
    url += `&search=${encodeURIComponent(search)}`;
  }
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Failed to fetch conversations: ${res.status}`);
  }

  return res.json();
}

export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/conversations/${conversationId}`,
    { method: "DELETE" },
  );

  if (!res.ok) {
    throw new Error(`Failed to delete conversation: ${res.status}`);
  }
}

export interface HistoryEvent {
  readonly type: string;
  readonly data: Record<string, unknown>;
  readonly timestamp: string;
  readonly iteration: number | null;
}

export interface ConversationEventsResponse {
  readonly events: readonly HistoryEvent[];
}

export async function fetchEvents(
  conversationId: string,
): Promise<ConversationEventsResponse> {
  const res = await fetch(
    `${API_BASE}/conversations/${conversationId}/events/history`,
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch events: ${res.status}`);
  }

  return res.json();
}

export async function fetchMessages(
  conversationId: string,
): Promise<ConversationMessagesResponse> {
  const res = await fetch(
    `${API_BASE}/conversations/${conversationId}/messages`,
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch messages: ${res.status}`);
  }

  return res.json();
}
