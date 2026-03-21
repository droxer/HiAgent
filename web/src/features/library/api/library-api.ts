import { API_BASE } from "@/shared/constants";
import type { LibraryResponse } from "../types";

export async function fetchLibrary(
  limit: number,
  offset: number,
): Promise<LibraryResponse> {
  const res = await fetch(
    `${API_BASE}/library?limit=${limit}&offset=${offset}`,
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch library: ${res.status}`);
  }
  return res.json();
}
