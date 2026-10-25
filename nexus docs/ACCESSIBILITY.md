# NEXUS accessibility requirements

Target WCAG 2.2 AA where applicable; do not claim compliance before testing.

- Use semantic landmarks, one logical H1, ordered heading levels, labels, native buttons/inputs, and descriptive links.
- All functions are keyboard operable with visible focus and logical focus order.
- Dialogs trap focus, close with Escape where appropriate, and return focus to their trigger.
- Error text is associated with its field; async run status is announced without interrupting typed input.
- Do not rely on colour for agent/run status. Maintain text alternatives for graphs and images.
- Meet contrast targets, support 200% zoom/reflow, and respect reduced motion.

**Verification:** automated axe/Lighthouse checks plus manual keyboard, screen-reader, zoom, contrast, and mobile tests on implemented pages.
