export type EventType =
  | "task_start"
  | "task_complete"
  | "task_error"
  | "turn_start"
  | "turn_complete"
  | "iteration_start"
  | "iteration_complete"
  | "llm_request"
  | "llm_response"
  | "text_delta"
  | "tool_call"
  | "tool_result"
  | "message_user"
  | "ask_user"
  | "user_response"
  | "agent_spawn"
  | "agent_complete"
  | "thinking"
  | "sandbox_stdout"
  | "sandbox_stderr"
  | "code_result";

export interface AgentEvent {
  type: EventType;
  data: Record<string, unknown>;
  timestamp: number;
  iteration: number | null;
}

export type TaskState = "idle" | "planning" | "executing" | "complete" | "error";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface ToolCallInfo {
  id: string;
  name: string;
  input: Record<string, unknown>;
  output?: string;
  success?: boolean;
  timestamp: number;
}

export interface AgentStatus {
  agentId: string;
  description: string;
  status: "running" | "complete" | "error";
}
