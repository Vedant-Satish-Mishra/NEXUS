# NEXUS animation and microinteraction rules

Use motion to confirm a result or orient a user, never to delay work. Proposed durations: 100–150ms for hover/focus, 150–220ms for small panels, and 180–280ms for dialogs/drawers. Prefer opacity and transform; avoid layout-thrashing properties, parallax, cursor effects, and auto-playing decorative motion.

- Buttons: quick press feedback; disabled controls do not animate as available.
- Loading: stream text and show node progress honestly; never add fake waiting time.
- Dialog/drawer: fade/slide with immediate focus transfer.
- Plan/tool cards: small state transition when waiting, approved, denied, or failed.
- Reduced motion: honour `prefers-reduced-motion`; make transitions effectively instant and avoid graph pulses.

Verify with browser performance tools once a frontend exists.
