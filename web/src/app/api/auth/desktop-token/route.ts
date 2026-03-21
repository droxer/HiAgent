import { NextResponse } from "next/server";

/**
 * In-memory store for desktop auth sessions.
 * Maps nonce → { user data, expiry }.
 * Short-lived (120s) and single-use.
 */
const pendingSessions = new Map<
  string,
  { user: { email: string; name: string; image: string; googleId: string }; expiresAt: number }
>();

// Clean up expired entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [key, value] of pendingSessions) {
    if (value.expiresAt < now) {
      pendingSessions.delete(key);
    }
  }
}, 10_000);

/**
 * POST /api/auth/desktop-token
 * Called by the desktop callback page (in the system browser) after
 * successful OAuth. Stores user data under the provided nonce.
 *
 * Body: { nonce, email, name?, image?, googleId? }
 */
export async function POST(req: Request) {
  const body = await req.json();
  const { nonce, email, name, image, googleId } = body;

  if (!nonce || !email) {
    return NextResponse.json({ error: "Missing nonce or email" }, { status: 400 });
  }

  pendingSessions.set(nonce, {
    user: { email, name: name ?? "", image: image ?? "", googleId: googleId ?? "" },
    expiresAt: Date.now() + 120_000,
  });

  return NextResponse.json({ ok: true });
}

/**
 * GET /api/auth/desktop-token?nonce=xxx
 * Called by the Tauri webview to check if OAuth completed.
 * Returns the user info if available, 404 otherwise.
 * Single-use: deletes the entry after successful retrieval.
 */
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const nonce = searchParams.get("nonce");

  if (!nonce) {
    return NextResponse.json({ error: "Missing nonce" }, { status: 400 });
  }

  const entry = pendingSessions.get(nonce);
  if (!entry || entry.expiresAt < Date.now()) {
    pendingSessions.delete(nonce ?? "");
    return NextResponse.json({ status: "pending" }, { status: 404 });
  }

  pendingSessions.delete(nonce);
  return NextResponse.json({ status: "complete", user: entry.user });
}
