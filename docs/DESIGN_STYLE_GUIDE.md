# HiAgent Design Style Guide

> Warm editorial aesthetic — refined, intentional, never generic.

---

## Aesthetic Direction

HiAgent follows a **warm editorial** tone: think high-end magazine meets productivity tool. The palette is built on natural stone tones with precise accent colors. Typography pairs a humanist sans-serif (Noto Sans) with an elegant serif (Instrument Serif) for display. Motion is purposeful — it communicates state, not decoration.

---

## Color System

### Core Palette

| Token | Hex | Role |
|-------|-----|------|
| `background` | `#FAF9F7` | Page canvas — warm off-white |
| `foreground` | `#1C1917` | Primary text — warm near-black |
| `primary` | `#1C1917` | Action buttons, interactive fills |
| `primary-foreground` | `#FAFAF9` | Text on primary surfaces |
| `secondary` | `#F0EEEA` | Muted backgrounds, user message bubbles |
| `secondary-foreground` | `#1C1917` | Text on secondary surfaces |
| `muted` | `#F0EEEA` | Inactive/disabled backgrounds |
| `muted-foreground` | `#78716C` | Secondary text, hints, timestamps |
| `card` | `#FFFFFF` | Card/elevated surfaces |
| `destructive` | `#DC2626` | Error states, delete actions |

### Borders

| Token | Hex | Usage |
|-------|-----|-------|
| `border` | `#E7E5E4` | Default borders, dividers |
| `border-strong` | `#D6D3D1` | Emphasized borders, user bubbles |
| `border-active` | `#78716C` | Focus state, active input borders |
| `input` | `#E7E5E4` | Input field borders |

### Accent Colors

Used sparingly for status indicators and semantic meaning. Never as dominant surface colors.

| Token | Hex | Semantic |
|-------|-----|----------|
| `accent-blue` | `#2563EB` | Links, info, processing |
| `accent-emerald` | `#059669` | Success, running, progress |
| `accent-amber` | `#D97706` | Warning, thinking |
| `accent-rose` | `#E11D48` | Error, failure |
| `accent-purple` | `#7C3AED` | Tool execution |

### Terminal (Dark Panel)

The right-side computer panel inverts the palette:

| Token | Hex |
|-------|-----|
| `terminal-bg` | `#1C1917` |
| `terminal-surface` | `#292524` |
| `terminal-border` | `#44403C` |
| `terminal-text` | `#D6D3D1` |
| `terminal-dim` | `#78716C` |

### Sidebar

| Token | Hex |
|-------|-----|
| `sidebar-bg` | `#FFFFFF` |
| `sidebar-active` | `#F0EEEA` |
| `sidebar-hover` | `#F7F6F4` |

### Design Rule: No Dark User-Facing Bubbles

User message bubbles use `bg-secondary` with `border-border-strong` — staying consistent with the warm light palette. Dark backgrounds are reserved exclusively for the terminal panel.

---

## Typography

### Font Stack

| Role | Font | Variable | Fallback |
|------|------|----------|----------|
| Body (sans) | Noto Sans | `--font-noto-sans` | system-ui, -apple-system, sans-serif |
| Display (serif) | Instrument Serif | `--font-instrument-serif` | Georgia, Times New Roman, serif |
| Code (mono) | System mono | — | SFMono, Menlo, Consolas |

### Type Scale

| Name | Size | Line Height | Usage |
|------|------|-------------|-------|
| Hero | `3.75rem` (60px) | 1.1 | Welcome screen heading |
| Heading | `1.125rem` (18px) | 1.3 | Section titles |
| Body | `0.875rem` (14px) | relaxed | Chat messages, UI text |
| Caption | `0.6875rem` (11px) | 1.45 | Timestamps, metadata |
| Micro | `0.625rem` (10px) | 1.4 | Inline badges, fine print |

### Weight & Tracking

| Class | Usage |
|-------|-------|
| `font-normal` | Serif headings (Instrument Serif is already bold by nature) |
| `font-medium` | Interactive elements — buttons, badges, message text |
| `font-semibold` | Card titles, section headers |
| `font-bold` | Logo, major headings |
| `tracking-tight` | Serif display headings |
| `tracking-[-0.01em]` | Chat message text (micro-tightening) |

### Rendering

Applied globally:
```css
-webkit-font-smoothing: antialiased;
-moz-osx-font-smoothing: grayscale;
text-rendering: optimizeLegibility;
```

---

## Spacing

Based on a **4px grid**. Key stops:

| Tailwind | Pixels | Usage |
|----------|--------|-------|
| `gap-1.5` / `p-1.5` | 6px | Tight element groups |
| `gap-2` / `p-2` | 8px | Standard inline spacing |
| `gap-3` / `p-3` | 12px | Input padding, compact sections |
| `p-4` / `px-4` | 16px | Chat bubble content padding |
| `gap-5` / `space-y-5` | 20px | Message vertical rhythm |
| `p-6` / `px-6` | 24px | Card padding, panel gutters |

### Key Patterns

- **Card content:** `px-6 py-6` (generous breathing room)
- **Chat messages:** `px-4 py-3.5` inside bubble, `space-y-5` between messages
- **Button with icon:** `gap-2` between icon and label
- **Form inputs:** `px-3 py-1` (compact, functional)
- **Sidebar items:** `px-3 py-2` with `gap-2.5`

---

## Border Radius

| Token | Size | Usage |
|-------|------|-------|
| `rounded` | 4px | Inline code |
| `rounded-md` | 6px | Inputs, badges, code blocks |
| `rounded-lg` | 8px | Buttons, dialogs |
| `rounded-xl` | 12px | Cards, panels |
| `rounded-2xl` | 16px | Chat bubbles, welcome input |
| `rounded-full` | 50% | Avatars, pills, status dots |

### Chat Bubble Radius

User messages use `rounded-2xl rounded-br-md` — all corners large except bottom-right, creating a chat-tail effect pointing toward the sender.

---

## Shadows

Three tiers of elevation:

| Name | Value | Usage |
|------|-------|-------|
| `shadow-card` | `0 1px 3px rgba(28,25,23,0.04), 0 1px 2px rgba(28,25,23,0.02)` | Cards at rest, user bubbles |
| `shadow-card-hover` | `0 4px 12px rgba(28,25,23,0.06), 0 1px 3px rgba(28,25,23,0.04)` | Cards on hover, focused inputs |
| `shadow-elevated` | `0 8px 24px rgba(28,25,23,0.08), 0 2px 8px rgba(28,25,23,0.04)` | Modals, dropdowns, popovers |

All shadows use `rgba(28, 25, 23, ...)` (the foreground color at low opacity) — never pure black. This keeps shadows warm and consistent with the stone palette.

### Focus Ring

```
focus-visible:border-ring
focus-visible:ring-[3px]
focus-visible:ring-ring/50
```

3px ring using `--color-ring` (#1C1917) at 50% opacity.

---

## Motion

### Library

Framer Motion (`framer-motion`) for React components. CSS `@keyframes` for pure-CSS animations.

### Timing Presets

| Speed | Duration | Usage |
|-------|----------|-------|
| Fast | `0.15s – 0.2s` | Micro-interactions, hover states |
| Standard | `0.3s – 0.4s` | Page transitions, fade-ins |
| Slow | `1.5s – 3s` | Continuous loops (pulse, rotate) |

### Core Patterns

**1. Fade + Slide Up (entrance)**
```tsx
initial={{ opacity: 0, y: 8 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.15, ease: "easeOut" }}
```

**2. Staggered Children**
```tsx
staggerChildren: 0.05
delayChildren: 0.3
```

**3. Spring Physics (progress, expand/collapse)**
```tsx
transition={{ type: "spring", stiffness: 300, damping: 25 }}
```

**4. Pulse (status indicator)**
```tsx
animate={{ scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }}
transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
```

**5. Typing Indicator (bouncing dots)**
```tsx
animate={{ y: [0, -4, 0] }}
transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
```

**6. Shadow Lift (hover — NOT scale)**
```tsx
whileHover={{
  boxShadow: "0 4px 12px rgba(28,25,23,0.10), 0 1px 3px rgba(28,25,23,0.06)",
}}
transition={{ duration: 0.2 }}
```

### Anti-Patterns

- **No `scale` on hover** for content elements (messages, cards). Scale is for buttons only (`active:scale-95`).
- **No gratuitous entrance animations**. Reserve motion for state changes.
- **Respect reduced motion:**
  ```css
  @media (prefers-reduced-motion: reduce) {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
  ```

---

## CSS Animations

Defined in `globals.css` inside `@theme`:

| Name | Usage |
|------|-------|
| `fadeIn` | Generic opacity entrance (0.3s) |
| `slideUp` | Content appearing from below (0.4s, 12px translate) |
| `slideInRight` | Panel sliding in from right (0.3s, 12px translate) |
| `shimmer` | Loading skeleton background sweep (2s, infinite) |

---

## Icons

### Library

Lucide React (`lucide-react`)

### Sizes

| Class | Pixels | Context |
|-------|--------|---------|
| `h-3 w-3` | 12px | Tiny indicators, copy button |
| `h-3.5 w-3.5` | 14px | Standard inline icons, send button |
| `h-4 w-4` | 16px | Menu items, toolbar buttons |
| `h-5 w-5` | 20px | Status indicators, large actions |

### Color States

| State | Class |
|-------|-------|
| Default | `text-muted-foreground` |
| Hover | `hover:text-foreground` |
| Active | `text-foreground` |
| Success | `text-accent-emerald` |
| Error | `text-accent-rose` |
| Info | `text-accent-blue` |

### Accessibility

Icons must always have either:
- Visible text label alongside, or
- `aria-label` on the parent button

---

## Component Patterns

### Buttons

Variants: `default`, `secondary`, `outline`, `ghost`, `destructive`, `link`

Sizes: `default` (h-9), `sm` (h-8), `lg` (h-10), `xs` (h-6), `icon` (square), `icon-sm`, `icon-xs`, `icon-lg`

```tsx
// Primary action
<Button variant="default">Submit</Button>

// Icon button with tooltip
<Tooltip>
  <TooltipTrigger asChild>
    <Button variant="ghost" size="icon-sm">
      <Plus className="h-4 w-4" />
    </Button>
  </TooltipTrigger>
  <TooltipContent>Add new</TooltipContent>
</Tooltip>
```

### Cards

```tsx
<Card>           {/* rounded-xl border bg-card py-6 shadow-sm */}
  <CardHeader>   {/* px-6 gap-2 */}
    <CardTitle />
    <CardDescription />
  </CardHeader>
  <CardContent>  {/* px-6 */}
  <CardFooter>   {/* px-6 */}
</Card>
```

### Inputs

- Height: `h-9` (36px)
- Border: `border-input`, focus: `border-ring` with 3px ring
- Background: transparent
- Text: `text-base` mobile, `md:text-sm` desktop

### Chat Input

- Dynamic height textarea (max 160px)
- Custom shadow focus state (not ring-based)
- Bottom toolbar: hint text + action buttons

### User Message Bubble

```tsx
<div className={cn("max-w-[80%]", msg.content.length < 60 && "max-w-fit")}>
  <motion.div
    className="rounded-2xl rounded-br-md border border-border-strong bg-secondary
               px-4 py-3.5 text-sm font-medium leading-relaxed
               tracking-[-0.01em] text-foreground"
    style={{ boxShadow: "..." }}
    whileHover={{ boxShadow: "..." }}
    transition={{ duration: 0.2 }}
  >
    <p className="whitespace-pre-wrap">
      {msg.content}
      <span className="... text-[10px] text-muted-foreground/50 ...">
        {timestamp}
      </span>
    </p>
  </motion.div>
</div>
```

Key rules:
- `bg-secondary` (warm light) — never dark
- `border-border-strong` for definition
- Smart width: `max-w-fit` for short messages (< 60 chars)
- Inline timestamp as subtle suffix
- Shadow lift on hover, no scale

### Assistant Message

Plain text with markdown rendering. No bubble, no border — just `text-sm leading-relaxed text-foreground` with `MarkdownRenderer`.

### Status Dots

```tsx
const STATUS_DOT_COLORS = {
  running: "bg-amber-500",
  complete: "bg-emerald-500",
  error: "bg-rose-500",
};
// Size: h-1 w-1 rounded-full
```

---

## Layout

### Main Layout

60/40 split when computer panel is open:
- Left: Conversation (50% with panel, 100% without)
- Right: Agent Computer panel (50%, slides in from right)

### TopBar

- Fixed `h-12` (48px)
- Frosted glass: `bg-card/80 backdrop-blur-sm`
- Breadcrumb navigation

### Sidebar

- Expanded: `w-64` (256px)
- Collapsed: `w-12` (48px)
- Transition: `transition-[width] duration-200 ease-in-out`

### Content Centering

Chat messages are capped at `max-w-3xl` when panel is closed, full width when open.

---

## Scrollbar

Custom thin scrollbar matching the stone palette:

```css
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(120, 113, 108, 0.2);
  border-radius: 9999px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(120, 113, 108, 0.4);
}
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `framer-motion` | ^12.36.0 | Animation |
| `lucide-react` | ^0.577.0 | Icons |
| `@radix-ui/*` | ^1.x | Accessible UI primitives |
| `class-variance-authority` | ^0.7.1 | Component variants |
| `tailwindcss` | ^4.1.0 | Utility CSS |
| `tailwind-merge` | ^3.5.0 | Class conflict resolution |
| `react-markdown` | ^10.1.0 | Markdown rendering |
| `rehype-highlight` | ^7.0.2 | Code syntax highlighting |
| `sonner` | ^2.0.7 | Toast notifications |

---

## Utility: `cn()`

All conditional class merging uses `cn()` from `@/shared/lib/utils`:

```tsx
import { cn } from "@/shared/lib/utils";
// Merges Tailwind classes intelligently, resolving conflicts
<div className={cn("base-class", condition && "conditional-class")} />
```

---

## File Organization

```
web/src/
  app/
    globals.css          # Theme tokens, keyframes, base styles
    fonts.ts             # Font configuration (Noto Sans, Instrument Serif)
    layout.tsx           # Root layout with font injection
  shared/
    components/
      ui/                # 28 shadcn/ui base components
      IconButton.tsx     # Button + Tooltip wrapper
      MarkdownRenderer.tsx
      Sidebar.tsx
      TopBar.tsx
    lib/
      utils.ts           # cn() helper
  features/
    conversation/        # Chat UI components
    agent-computer/      # Terminal/tool panel components
```
