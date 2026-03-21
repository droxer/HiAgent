# HiAgent Desktop App

HiAgent Desktop wraps the existing web frontend in a [Tauri v2](https://v2.tauri.app/) native shell, giving you a standalone macOS/Windows/Linux application with no browser tab required.

## Architecture

```
┌──────────────────────────────────┐
│         Tauri Desktop Shell      │
│  ┌────────────────────────────┐  │
│  │   WKWebView / WebView2    │  │
│  │   (loads localhost:3000)   │  │
│  └────────────┬───────────────┘  │
│               │                  │
│  ┌────────────▼───────────────┐  │
│  │   Sidecar Process Manager  │  │
│  │   (Rust / tokio)           │  │
│  └──────┬────────────┬────────┘  │
│         │            │           │
│    ┌────▼────┐  ┌────▼────┐     │
│    │ Next.js │  │ FastAPI │     │
│    │ :3000   │  │ :8000   │     │
│    └─────────┘  └─────────┘     │
└──────────────────────────────────┘
```

The desktop app runs both the Next.js frontend and Python backend as **sidecar processes** managed by Tauri's Rust layer. This means:

- Zero changes to the existing web codebase
- Auth, SSE streaming, API proxy all work as-is
- Sidecars are auto-started on launch and cleaned up on quit
- If a port is already in use (e.g. you ran `make dev`), the sidecar is skipped

## Prerequisites

- **Rust** 1.77+ (`rustup` or Homebrew)
- **Node.js** with npm
- **Python 3.12+** with `uv`
- **macOS**: Xcode Command Line Tools (`xcode-select --install`)

## Quick Start

```bash
# Dev mode — opens Tauri window with hot reload
make desktop

# Production build — creates .app bundle
make build-desktop
```

The production `.app` is output to:

```
web/src-tauri/target/release/bundle/macos/HiAgent.app
```

## Configuration

All settings are driven by environment variables with sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `HIAGENT_FRONTEND_PORT` | `3000` | Port for the Next.js frontend |
| `HIAGENT_BACKEND_PORT` | `8000` | Port for the Python backend |
| `HIAGENT_PROJECT_DIR` | auto-detected | Path to the HiAgent repo root |

### Custom ports

```bash
HIAGENT_FRONTEND_PORT=4000 HIAGENT_BACKEND_PORT=9000 make desktop
```

### Backend environment

The backend still reads its own `.env` file from `backend/.env`. See `backend/.env.example` for required variables (`ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, etc.).

## Google OAuth (System Browser)

The desktop app opens Google OAuth in the **system browser** instead of the embedded webview. This is required because Google blocks OAuth in embedded webviews.

### Flow

1. User clicks "Sign in with Google" in the Tauri window
2. System browser opens → Google OAuth consent screen
3. Auth completes → NextAuth redirects to `/auth/desktop-callback`
4. Callback page triggers `hiagent://auth/callback` deep link
5. Tauri captures the deep link → reloads the webview with the active session

### Setup

The `hiagent://` URL scheme is registered via Tauri's deep link plugin. On macOS, this is handled automatically via the app's `Info.plist`. On first launch, macOS may prompt for permission to open the custom URL scheme.

Your Google OAuth credentials need `http://localhost:3000/api/auth/callback/google` (or your custom port) as an authorized redirect URI in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).

## Project Structure

```
web/
├── src-tauri/                    # Tauri desktop shell
│   ├── Cargo.toml                # Rust dependencies
│   ├── build.rs                  # Tauri build script
│   ├── tauri.conf.json           # Window size, CSP, plugins, bundle config
│   ├── capabilities/
│   │   └── default.json          # Permissions (shell, deep-link)
│   ├── icons/                    # Generated app icons (all platforms)
│   └── src/
│       ├── main.rs               # Entry point
│       ├── lib.rs                # Tauri setup, plugin registration, event handlers
│       ├── config.rs             # Env-based configuration (ports, project dir)
│       └── sidecar.rs            # Process manager for backend + frontend
├── dist/
│   └── index.html                # Loading screen (shown while sidecars start)
├── src/
│   ├── lib/tauri.ts              # Frontend Tauri utilities (isTauri, openInSystemBrowser)
│   └── app/auth/desktop-callback/
│       └── page.tsx              # OAuth callback → deep link trigger
└── package.json                  # Includes tauri:dev and tauri:build scripts
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make desktop` | Start Tauri in dev mode (hot reload) |
| `make build-desktop` | Build production `.app` bundle |

## Troubleshooting

### Port already in use

The sidecar manager checks if ports are occupied before starting. If you already have `make dev` running, the desktop app will connect to the existing services instead of starting new ones.

### Backend fails to start

Check that `backend/.env` exists with valid API keys. You can also start the backend manually and let the desktop app detect it:

```bash
make backend &
make desktop
```

### DMG bundling fails

The DMG bundler requires `create-dmg`. Install it or stick with the `.app` output:

```bash
brew install create-dmg
```

The bundle target is set to `app` only by default. To enable DMG, change `targets` in `tauri.conf.json`:

```json
"targets": ["app", "dmg"]
```

### OAuth redirect mismatch

Ensure your Google OAuth client has `http://localhost:<HIAGENT_FRONTEND_PORT>/api/auth/callback/google` as an authorized redirect URI.
