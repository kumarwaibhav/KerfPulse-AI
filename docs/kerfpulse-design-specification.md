# UI/UX DESIGN SYSTEM SPECIFICATION: KERFPULSE AI ("WARM INDUSTRIAL PRECISION")

## 1. Core Aesthetic Philosophy
Design and build a unified, dual-theme (Light + Dark) enterprise B2B SaaS interface for **KerfPulse AI** (*"Precision in every signal. Certainty in every shift."*). The visual language merges two distinct industrial benchmarks into one seamless system:
- **Light Theme ("Daylight Digital Twin" — Default for Executive Overview & Planning):** Inspired by European industrial design (Velluto Smart Factory). Uses warm off-white, stone, and soft beige/alabaster surfaces—never sterile hospital-white (`#FFFFFF`) as a full-screen background. Features architectural isometric 3D wireframe/clay grids, soft diffused shadows, and frosted white glassmorphic floating HUD cards.
- **Dark Theme ("Night-Shift Telemetry" — Default for Shop-Floor & High-Frequency Waveforms):** Inspired by modern enterprise AI systems (96AI). Uses deep matte obsidian and warm charcoal surfaces—never pure `#000000`—paired with subtle dark smoked-glass panels, 1px specular top-edge highlights, and a soft ambient radial ember glow behind hero/3D focal points.
- **Unifying Brand Accent:** Both themes share **Forge Vermilion / Industrial Orange (`#F05A28` in Light, `#FF6B35` in Dark)** for primary CTAs, active machine selection hotspots, progress fills, and selective 25 kHz vibration gate triggers.

## 2. Semantic Color & Glassmorphism Tokens (CSS Variables)
Implement strict CSS custom properties toggled via `data-theme="light"` and `data-theme="dark"` with smooth 200ms color transitions:

### Light Mode ("Warm Stone & Frosted Alabaster")
- `--bg-canvas`: `#F4F2EE` (Warm off-white / architectural stone-beige base)
- `--bg-canvas-secondary`: `#EBE8E2` (Subtle recessed tray for bottom machine strips & table headers)
- `--bg-surface-solid`: `#FAF9F6` (Crisp warm alabaster for standard Bento analytics cards)
- `--bg-glass`: `rgba(252, 250, 247, 0.72)` with `backdrop-filter: blur(16px) saturate(140%)` (Floating HUD popovers over the 3D CNC canvas, active work-order drawer)
- `--border-glass`: `1px solid rgba(255, 255, 255, 0.85)` + outer hairline `0 1px 2px rgba(24, 24, 27, 0.06)`
- `--border-subtle`: `#E2DDD5` (Warm architectural CAD grid lines and dividers)
- `--text-primary`: `#18181B` (Deep carbon ink)
- `--text-secondary`: `#6B6860` (Warm machined slate for timestamps, `42CrMo4` recipe tags, and cut metadata)
- `--accent-primary`: `#EA580C` / `#F05A28` (Industrial Vermilion Orange — active bars, hotspot pulse, primary buttons)
- `--shadow-elevated`: `0 12px 32px -8px rgba(28, 25, 23, 0.08)`

### Dark Mode ("Matte Obsidian & Smoked Ember Glass")
- `--bg-canvas`: `#0B0C0E` (Deep matte obsidian base)
- `--bg-canvas-secondary`: `#111317` (Recessed machine dock & secondary panels)
- `--bg-surface-solid`: `#15181E` (Elevated slate-charcoal Bento cards)
- `--bg-glass`: `rgba(22, 25, 32, 0.68)` with `backdrop-filter: blur(18px) saturate(130%)` (Smoked translucent HUD overlays)
- `--border-glass`: `1px solid rgba(255, 255, 255, 0.09)` (Crisp 1px specular rim light)
- `--border-subtle`: `rgba(255, 255, 255, 0.06)` (Isometric 3D floor grid lines)
- `--text-primary`: `#F5F5F4` (Warm titanium off-white)
- `--text-secondary`: `#9CA3AF` (Muted alloy gray)
- `--accent-primary`: `#FF6B35` (Luminous Forge Orange — pops cleanly against dark glass)
- `--hero-ambient-glow`: `radial-gradient(circle at 50% 35%, rgba(240, 90, 40, 0.12), transparent 65%)`

### Shared Semantic Status Tokens (Consistent Meaning Across Both Themes)
- **Nominal Cut / Running:** Emerald (`#10B981` Dark / `#059669` Light) — tiny 6px glowing status dot + text label (`• Running`).
- **25 kHz Selective Vibration Gate Fired / Budget Spent:** Amber-Gold (`#F59E0B` Dark / `#D97706` Light).
- **Actionable Cutter Damage Risk (`2–5 cuts` window):** Crimson-Red (`#EF4444` Dark / `#DC2626` Light) — reserved strictly for verified damage-horizon warnings so it never clashes with the orange brand accent.
- **Abstention / Missing Cut:** Warm Gray (`#78716C`).

## 3. Spatial Layout, 3D Grid & Component Architecture
1. **Ultra-Clean Navigation Shell:**
   - **Left Slim Icon Rail (`64px` wide):** Minimal monochrome stroke icons; active route highlighted with a soft warm-orange pill (`rgba(240, 90, 40, 0.12)`) and `--accent-primary` icon stroke.
   - **Top Header Bar (`60px` high):** Brand mark (**KerfPulse AI**), current view title + live pulse dot (`Recorded telemetry replay`), segmented Light/Dark theme switcher pill, MQTT QoS 1 connection badge, and user role indicator (`Operator` / `Planner` / `Reliability Engineer`).

2. **View A — Spatial 3D CNC Digital Twin & Live Cut Replay (Primary Shop-Floor View):**
   - **Background Isometric Stage:** Full-bleed interactive isometric 3D/SVG architectural grid showing the Haas CNC machining testbed (`42CrMo4` steel milling). In Light Mode, render crisp architectural wireframe walls and clay-shaded grey machinery; in Dark Mode, render dark matte metallic geometry over a subtle glowing isometric CAD grid.
   - **Interactive Hotspot & Floating Glass Popover:** Place a pulsing `--accent-primary` orange beacon directly on the active CNC spindle/cutter. Clicking or hovering opens a **frosted glassmorphic card** (`rounded-2xl`, `--bg-glass`) displaying Tool ID (`Tool #01–#14`), Current Cycle (`Cycle 034`), Recipe settings, 500 Hz Motor Current risk score, and Remaining Vibration Budget (`floor(n/4)`).
   - **Right Floating Glass Drawer ("Inspection Queue & Active Work Orders"):** Collapsible translucent panel listing upcoming feasible production breaks, horizontal orange progress bars for cut-window urgency, and one-click `Approve` / `Dismiss` / `Complete` planner transitions.
   - **Bottom Horizontal Asset Dock:** 4-column card strip at the bottom edge showing individual cutter runs / policy comparisons (*Periodic Every-4th-Cut* vs. *KerfPulse Decision-Aware Policy*) with clean monochrome 3D machine/tool thumbnails, operator/run metadata, and status pills.

3. **View B — Executive Overview & Evaluation Bento Grid (Analytics & Paper Metrics View):**
   - Structured 3-column asymmetric Bento grid with `20px` rounded corners (`rounded-2xl`) and generous `24px` whitespace padding.
   - **Hero KPI Strip:** Large, ultra-light tabular numerals (`48px` font-light, `JetBrains Mono` / `Plus Jakarta Sans` with `tabular-nums`) for Timely Coverage %, Premature Reviews per 100 Cuts, Saved Vibration Payload Bytes, and Lead Cuts Before Breakage—with small green/orange delta badges underneath.
   - **Smooth Dual-Spline ECharts Canvas:** Clean spline/area curves comparing predicted benchmark risk vs. inspection threshold over sequential cuts, with subtle vertical dashed markers (`--accent-primary`) where selective 25 kHz vibration was requested, and floating glass tooltips on hover.
   - **Actionable Events Table:** Clean borderless row layout with pill filter tabs (`All`, `Actionable Window`, `Budget Deferred`, `Completed`) and a solid pill CTA button in `--accent-primary` orange.

## 4. Typography & Motion Rules (Framer Motion)
- **Headings & UI:** `Plus Jakarta Sans` or `Inter` (tight tracking `-0.02em` on large headers like `Shift B` or `Overview`).
- **Telemetry, Cut Ordinals & KPIs:** `JetBrains Mono` or `Geist Mono` with `font-variant-numeric: tabular-nums` so streaming MQTT numbers never shift layout width.
- **Motion:** Use mechanical, damped spring transitions (`stiffness: 380, damping: 32`) for glass popover entrances, theme switching, and live progress-bar updates—never bouncy or sluggish animations.
