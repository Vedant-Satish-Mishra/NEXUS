# NEXUS design system

The design system matches the approved visual direction shown in `nexus frontend/` design mockups and `NEXUS_FRONTEND_DESIGN.md`.

```css
:root {
  /* Dark cocoa background & dark surfaces */
  --nx-bg: #1a120b;
  --nx-bg-subtle: #241812;
  --nx-surface-dark: #2c1e16;
  --nx-border-dark: #3d2b20;

  /* Warm cream content panels & card surfaces */
  --nx-panel: #fdfbf7;
  --nx-panel-subtle: #f7f2ea;
  --nx-panel-hover: #f1ebd8;
  --nx-border: #e6decb;
  --nx-border-card: #d8cbb8;

  /* Text colors */
  --nx-text: #1e140f;
  --nx-text-muted: #6e5849;
  --nx-text-inverse: #fdfbf7;
  --nx-text-inverse-muted: #a89485;

  /* Accents & brand colors */
  --nx-primary: #ea580c;
  --nx-primary-hover: #c2410c;
  --nx-primary-subtle: #fff1eb;
  --nx-gold: #d97706;
  --nx-gold-subtle: #fef3c7;
  --nx-danger: #dc2626;
  --nx-danger-subtle: #fee2e2;
  --nx-success: #16a34a;
  --nx-success-subtle: #dcfce7;
  --nx-focus: #f97316;

  /* Spacing */
  --nx-space-1: 0.25rem;
  --nx-space-2: 0.5rem;
  --nx-space-3: 0.75rem;
  --nx-space-4: 1rem;
  --nx-space-5: 1.25rem;
  --nx-space-6: 1.5rem;
  --nx-space-8: 2rem;

  /* Radii */
  --nx-radius-sm: 0.5rem;
  --nx-radius-md: 0.875rem;
  --nx-radius-lg: 1.25rem;
  --nx-radius-xl: 1.5rem;
  --nx-content-max: 1440px;
}
```

## Type and layout

Use a readable sans-serif UI family with system fallbacks; reserve a display serif only for the brand wordmark/major editorial titles. Proposed type scale: 12, 14, 16, 20, 24, 32px with 1.4–1.6 body line height. Use a 4px spacing scale and 12-column desktop grid. Proposed breakpoints: 480, 768, 1024, 1280px; validate against real targets.

## Component rules

Buttons have primary, secondary, destructive, and ghost variants; minimum 44×44px touch target. Inputs, cards, dialogs, tables, badges, navigation, and focus rings reuse tokens. Use subtle 1px borders and tonal surfaces; shadows only for modal elevation, not routine cards. Meet WCAG 2.2 AA contrast, including interactive states.
