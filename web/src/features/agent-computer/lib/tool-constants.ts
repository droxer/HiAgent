/** Tools whose results are never considered "artifacts" for panel auto-open. */
export const NON_ARTIFACT_TOOLS = new Set([
  "web_search",
  "web_fetch",
  "ask_user",
  "message_user",
  "memory_store",
  "memory_recall",
  "task_complete",
]);

/** Tools whose output should be rendered as code. */
export const CODE_TOOLS = new Set([
  "code_run",
  "code_interpret",
  "shell_exec",
  "file_read",
]);
