# Tally Sync Platform — Design System Specification

> Visual design language, component patterns, and UX guidelines for the frontend.

---

## 1. Brand Identity

### 1.1 Product Personality
- **Trustworthy** — Financial data demands confidence
- **Modern** — Not "enterprise boring" — this is a new-age Indian SaaS
- **Approachable** — Target users are accountants, not developers
- **Efficient** — Every pixel should serve a purpose

### 1.2 Logo Usage
- Primary: Horizontal lockup (logo + "Tally Sync")
- Sidebar: Icon-only (collapsed state)
- Favicon: 32x32 icon variant

---

## 2. Color System

### 2.1 Primary Palette — Teal (Trust & Finance)

| Token | Hex | Usage |
|-------|-----|-------|
| `primary-50` | `#f0fdfa` | Background tints |
| `primary-100` | `#ccfbf1` | Hover states |
| `primary-200` | `#99f6e4` | Light borders |
| `primary-500` | `#14b8a6` | Primary buttons, links |
| `primary-600` | `#0d9488` | Button hover |
| `primary-700` | `#0f766e` | Active/pressed |
| `primary-900` | `#134e4a` | Dark text on teal bg |

### 2.2 Accent Palette — Amber (Attention & Indian Aesthetic)

| Token | Hex | Usage |
|-------|-----|-------|
| `accent-400` | `#fbbf24` | Highlights, badges |
| `accent-500` | `#f59e0b` | Warning indicators |
| `accent-600` | `#d97706` | Accent buttons |

### 2.3 Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `success` | `#22c55e` | Healthy sync, successful actions |
| `warning` | `#f59e0b` | Delayed sync, approaching limits |
| `error` | `#ef4444` | Failed sync, errors, destructive |
| `info` | `#3b82f6` | Informational messages |

### 2.4 Voucher Type Color Map

```typescript
const VOUCHER_COLORS: Record<VoucherType, { bg: string; text: string; border: string }> = {
  'Sales':       { bg: '#dcfce7', text: '#166534', border: '#86efac' },
  'Purchase':    { bg: '#dbeafe', text: '#1e3a8a', border: '#93c5fd' },
  'Receipt':     { bg: '#d1fae5', text: '#065f46', border: '#6ee7b7' },
  'Payment':     { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  'Journal':     { bg: '#f3e8ff', text: '#581c87', border: '#c4b5fd' },
  'Debit Note':  { bg: '#fef3c7', text: '#92400e', border: '#fcd34d' },
  'Credit Note': { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
};
```

---

## 3. Typography

### 3.1 Font Stack

| Usage | Font | Weight | Fallback |
|-------|------|--------|----------|
| Headings (h1–h3) | Outfit | 600–800 | system-ui |
| Body / UI | Inter | 400–600 | system-ui, sans-serif |
| Monospace / data | JetBrains Mono | 400 | Fira Code, monospace |
| Numbers / amounts | Inter Tabular | 500 | monospace |

### 3.2 Type Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Display (hero) | 3rem / 48px | 800 | 1.1 |
| H1 | 2rem / 32px | 700 | 1.2 |
| H2 | 1.5rem / 24px | 600 | 1.3 |
| H3 | 1.25rem / 20px | 600 | 1.4 |
| Body | 0.875rem / 14px | 400 | 1.5 |
| Small | 0.75rem / 12px | 400 | 1.4 |
| KPI Number | 2.5rem / 40px | 800 | 1.0 |
| Table Data | 0.8125rem / 13px | 400 | 1.4 |

### 3.3 Number Formatting Rules

| Type | Format | Example |
|------|--------|---------|
| Currency (INR) | Indian notation | ₹12,34,567 |
| Counts | Standard comma | 1,589 |
| Percentages | 1 decimal | 12.3% |
| Dates | DD MMM YYYY | 28 Jun 2026 |
| Relative Time | Human-readable | "2 hours ago" |

---

## 4. Spacing & Layout

### 4.1 Spacing Scale (8px base)

| Token | Size | Usage |
|-------|------|-------|
| `space-1` | 4px | Tight inline spacing |
| `space-2` | 8px | Icon-text gap |
| `space-3` | 12px | Small padding |
| `space-4` | 16px | Standard padding |
| `space-5` | 20px | Section gap |
| `space-6` | 24px | Card padding |
| `space-8` | 32px | Section spacing |
| `space-12` | 48px | Large section gap |
| `space-16` | 64px | Page section spacing |

### 4.2 Layout Grid

```
Desktop (> 1024px):
┌────────────┬──────────────────────────────────────┐
│  Sidebar   │  Content Area                        │
│  240px     │  flex-1                               │
│  fixed     │  max-width: 1280px                    │
│            │  padding: 24px                        │
└────────────┴──────────────────────────────────────┘

Tablet (640px – 1024px):
┌──┬─────────────────────────────────────────────────┐
│≡ │  Content (sidebar collapsed to icons)           │
│  │  padding: 16px                                  │
└──┴─────────────────────────────────────────────────┘

Mobile (< 640px):
┌─────────────────────────────────────────────────────┐
│  Header (hamburger + logo + user)                   │
│─────────────────────────────────────────────────────│
│  Content (full width, padding: 12px)                │
│                                                     │
│─────────────────────────────────────────────────────│
│  Bottom Nav (5 icons)                               │
└─────────────────────────────────────────────────────┘
```

---

## 5. Component Specifications

### 5.1 Sidebar

```
┌─────────────────┐
│  🔷 Tally Sync  │  ← Logo + name (hidden when collapsed)
│─────────────────│
│                 │
│  📊 Dashboard   │  ← Active: primary-500 bg, white text
│  📋 Vouchers    │  ← Hover: primary-100 bg
│  📖 Ledgers     │
│  🖥️ Devices     │
│  📡 Sync History│
│                 │
│─────────────────│
│  ⚙️ Settings    │
│  🚪 Logout      │
│─────────────────│
│  Collapse «     │  ← Toggle button
└─────────────────┘

Background: slate-900 (#0f172a)
Text: slate-300 (#cbd5e1)
Active item: primary-500 bg with white text
Hover: slate-800 bg
Width: 240px (expanded) / 64px (collapsed)
Transition: width 0.2s ease
```

### 5.2 KPI Card

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌──┐  Total Vouchers                  │
│  │📊│  ────────────────                │
│  └──┘  1,589                           │  ← Outfit 800, 2.5rem
│        ↑ 12% from last month           │  ← Green text + arrow
│                                         │
│  ▁▂▃▅▆▇█▇▆▅▃▂ (sparkline)             │  ← 40px height, primary color
│                                         │
└─────────────────────────────────────────┘

Border: 1px solid slate-200
Border-radius: 12px
Padding: 24px
Shadow: 0 1px 3px rgba(0,0,0,0.06)
Hover: translateY(-2px), shadow increases
Transition: all 0.2s ease
```

### 5.3 Data Table

```
┌──────────────────────────────────────────────────────────────┐
│  Vouchers                             🔍 Search  📥 Export  │
│──────────────────────────────────────────────────────────────│
│  Filter: [All Types ▾]  [Date Range ▾]  [Party Search]      │
│──────────────────────────────────────────────────────────────│
│  #     │ Date       │ Party           │ Amount    │ Type     │
│────────┼────────────┼─────────────────┼───────────┼──────────│
│  V-001 │ 28 Jun '26 │ Sharma Traders  │ ₹12,500  │ 🟢Sales │
│  V-002 │ 27 Jun '26 │ Patel Industries│ ₹45,000  │ 🔵Purch │
│  V-003 │ 27 Jun '26 │ Cash            │ ₹8,750   │ 💰Rcpt  │
│──────────────────────────────────────────────────────────────│
│  Showing 1–50 of 1,589        ◀ 1 2 3 ... 32 ▶             │
└──────────────────────────────────────────────────────────────┘

Header: slate-50 bg, 600 weight, sticky
Rows: Alternating white/slate-50
Hover: primary-50 bg
Selected: primary-100 bg + left border primary-500
Amounts: Right-aligned, tabular numbers, monospace
Type badges: Colored pills (see voucher color map)
```

### 5.4 Sync Health Indicator

```
Three states:

🟢 Healthy          🟡 Warning           🔴 Error
Last sync: 2h ago   Last sync: 3 days    No recent sync

Green pulsing dot   Amber slow blink     Red static dot
"All systems go"    "Agent may need      "Check agent
                     attention"           immediately"
```

CSS for pulsing dot:
```css
.sync-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.sync-dot--healthy {
  background: #22c55e;
  box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
  0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
  100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}
```

### 5.5 Device Card

```
┌─────────────────────────────────────────┐
│  OFFICE-PC-01                  🟢 Active│
│  ─────────────────────────────────────  │
│  💻 Windows 11 Build 26200             │
│  📦 Agent v0.4.0                       │
│  🕐 Last sync: 2 hours ago             │
│  🌐 IP: 192.168.1.100                  │
│                                         │
│  [🔄 Rotate Key]  [📊 Details]         │
└─────────────────────────────────────────┘

Layout: CSS Grid, 3 columns on desktop, 1 on mobile
Border: 1px solid slate-200
Border-radius: 12px
Status badge: top-right corner
```

---

## 6. Motion & Transitions

### 6.1 Timing

| Context | Duration | Easing |
|---------|----------|--------|
| Hover effects | 150ms | ease |
| Page transitions | 300ms | ease-out |
| Modal enter | 200ms | ease-out |
| Modal exit | 150ms | ease-in |
| Sidebar toggle | 200ms | ease |
| Toast notifications | 300ms enter, 200ms exit | ease |
| Loading skeleton | 1.5s shimmer | linear (infinite) |

### 6.2 Key Animations

- **Card hover**: `translateY(-2px)` + shadow increase
- **Button press**: `scale(0.98)` for 100ms
- **Page enter**: `fadeSlideIn` (opacity 0→1, translateY 8→0)
- **Sync pulse**: Concentric rings expanding from dot
- **Skeleton loader**: Left-to-right shimmer gradient
- **Toast**: Slide in from right, auto-dismiss after 5s

---

## 7. Empty States

Every page needs a graceful empty state:

| Page | Empty State Message | Icon | CTA |
|------|-------------------|------|-----|
| Dashboard (no data) | "No data synced yet. Set up your agent to get started." | 📊 BarChart3 | "Setup Guide" link |
| Vouchers (empty) | "No vouchers found. They'll appear here once your agent syncs." | 📋 FileText | "View Sync Status" |
| Devices (none) | "No devices registered. Install the agent on your PC." | 🖥️ Monitor | "Download Agent" button |
| Sync History (empty) | "No sync history yet. Your sync logs will appear here." | 📡 Radio | — |

---

## 8. Error States

### 8.1 API Error Banner
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  Unable to fetch dashboard data. Retrying in 30s...      │
│     [Try Again]  [View Details]                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Form Validation
- Inline red text below field: "This email is already registered"
- Red border on invalid field
- Shake animation on submit with errors

### 8.3 Toast Notifications

| Type | Color | Auto-dismiss |
|------|-------|-------------|
| Success | Green-500 left border | 5 seconds |
| Error | Red-500 left border | Manual dismiss |
| Warning | Amber-500 left border | 8 seconds |
| Info | Blue-500 left border | 5 seconds |

---

## 9. Accessibility

- All interactive elements must be keyboard-navigable
- Color contrast ratio ≥ 4.5:1 (WCAG AA)
- Focus rings: 2px solid primary-500, 2px offset
- `aria-labels` on icon-only buttons
- Screen reader announcements for toast notifications
- Reduced motion: Respect `prefers-reduced-motion: reduce`

---

## 10. Dark Mode

Support OS-level `prefers-color-scheme: dark` + manual toggle.

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| App background | `#f8fafc` | `#0f172a` |
| Card background | `#ffffff` | `#1e293b` |
| Sidebar | `#0f172a` | `#020617` |
| Text primary | `#1e293b` | `#f1f5f9` |
| Text secondary | `#64748b` | `#94a3b8` |
| Borders | `#e2e8f0` | `#334155` |
| Table row hover | `#f0fdfa` | `#0f2f2f` |
