# HiAgent Brand Guidelines

## Brand Identity

HiAgent is an intelligent AI agent platform. The brand communicates **capability**, **clarity**, and **calm confidence** through a premium dark-mode-first aesthetic with purposeful glassmorphic depth.

## Voice & Tone

- **Direct**: Short, confident statements. "What can I help you build?" not "Please describe what you'd like assistance with."
- **Anthropomorphic but not chatty**: "HiAgent's Computer" is a branded surface name. The agent has presence but isn't overly friendly.
- **Technical confidence**: Assume the user is capable. Don't over-explain.

## Colors

### Core Palette

| Token | Dark | Light | Usage |
|-------|------|-------|-------|
| `background` | `#0A0A0A` | `#FFFFFF` | Page background |
| `foreground` | `#EDEDED` | `#1A1A1A` | Primary text |
| `card` | `#141414` | `#FFFFFF` | Card surfaces |
| `border` | `#2A2A2A` | `#E4E4E7` | Default borders |
| `muted-foreground` | `#A1A1AA` | `#71717A` | Secondary text |

### Accent Colors

| Token | Dark | Light | Usage |
|-------|------|-------|-------|
| `ai-glow` | `#818CF8` (Indigo 400) | `#818CF8` | AI activity indicator, primary brand signal |
| `user-accent` | `#3B82F6` (Blue 500) | `#3B82F6` | User messages, input focus |
| `accent-emerald` | `#34D399` | `#10B981` | Success, completion |
| `accent-amber` | `#D97706` | `#B45309` | Warnings, caution |
| `accent-rose` | `#F87171` | `#EF4444` | Errors, destructive actions |
| `accent-purple` | `#7C3AED` | `#7C3AED` | Secondary AI accent |

### AI Glow Usage

The indigo `ai-glow` is the signature brand color. Use it for:
- Pulsing activity dots (agent running)
- Progress bar gradients
- Orbital pulse animations on active states
- Status indicators for AI activity

Do NOT use `ai-glow` for:
- Static decorative elements
- User-initiated actions
- Error states

## Typography

### Font Stack

| Family | Font | Usage |
|--------|------|-------|
| `--font-sans` | Inter | Body text, UI labels, buttons |
| `--font-serif` | Instrument Serif | Hero headings (WelcomeScreen) |
| `--font-mono` | JetBrains Mono | Code, terminal output, technical values |

### Type Scale

| Token | Size | Tailwind | Usage |
|-------|------|----------|-------|
| `hero` | 3.75rem | `text-6xl` | Welcome screen heading |
| `h1` | 1.5rem | `text-2xl` | Page titles |
| `h2` / `heading` | 1rem | `text-base` | Section headers |
| `body` | 0.875rem | `text-sm` | Body text, messages |
| `caption` | 0.75rem | `text-xs` | Labels, timestamps, metadata |
| `micro` | 0.625rem | `text-[10px]` | Keyboard shortcuts, badges |

### Hierarchy Rules

- Hero pages: `font-serif` + `text-6xl`
- Page titles: `font-sans` + `text-base font-semibold`
- Section headers: `font-sans` + `text-sm font-medium text-muted-foreground`
- Body: `font-sans` + `text-sm`

## Spacing & Radius

### Border Radius

| Element Type | Radius | Tailwind |
|-------------|--------|----------|
| Interactive elements (buttons, inputs) | 8px | `rounded-lg` |
| Containers (cards, panels, dialogs) | 12px | `rounded-xl` |
| Pills, tags, chips | 9999px | `rounded-full` |
| User message bubble (bottom-right) | 6px | `rounded-br-md` |

### Padding Convention

| Context | Padding | Tailwind |
|---------|---------|----------|
| Page containers | 24px | `px-6` |
| Sections, cards | 16px | `px-4` |
| Compact elements (sidebar items, chips) | 12px | `px-3` |
| Inline elements | 8px | `px-2` |

## Shadows

Use CSS variable-based shadows exclusively (never inline `style` for shadows):

| Token | Usage |
|-------|-------|
| `shadow-card` | Default card elevation |
| `shadow-card-hover` | Card hover state |
| `shadow-elevated` | Modals, command palette, dropdowns |

## Animations

### Principles

- Always respect `prefers-reduced-motion`
- Use spring physics for interactive elements
- Use `ease-out` for enter animations, `ease-in` for exits
- Standard duration: 200ms for micro-interactions, 300ms for reveals

### Standard Animations

| Name | Duration | Usage |
|------|----------|-------|
| `orbitalPulse` | 2s | AI activity dots (running state) |
| `shimmer` | 2s | Loading skeleton placeholders |
| `conicSpin` | 3s | Cancel button border animation |
| `fadeIn` | 0.3s | General element entry |
| `slideUp` | 0.4s | Bottom-up reveal |

### AI Pulsing Dot

Use the shared `<PulsingDot>` component for all AI activity indicators. Available sizes: `sm` (1.5px) and `md` (2px). Always use 2s duration for consistency.

## Components

### Buttons

Always use the `<Button>` component from `shared/components/ui/button`. Never use raw `<button>` elements with manual styling. Available variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`.

### Focus Rings

Standardize all focus indicators: `focus-visible:ring-[3px] focus-visible:ring-ring/50`

### Touch Targets

All interactive elements must have a minimum 44px touch target (WCAG). Use padding or `min-w`/`min-h` to achieve this for small icon buttons.

## Logo & Favicon

- Master logo: `public/logo.png`
- All favicon variants (`favicon.ico`, `favicon-16.png`, `favicon-32.png`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`) should be generated from the master logo
- PWA manifest colors: `theme_color: "#0A0A0A"`, `background_color: "#0A0A0A"`
