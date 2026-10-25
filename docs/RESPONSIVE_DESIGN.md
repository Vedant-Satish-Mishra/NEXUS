# NEXUS responsive design

Use mobile-first implementation. Proposed layout behaviour: small phones <480px, phones 480–767px, tablets 768–1023px, laptop 1024–1279px, wide ≥1280px; validate against actual browser requirements once known.

- Small/large phones: one chat column; sidebar and agents/sources as sheets; forms single column; no horizontal scrolling.
- Tablets: persistent compact navigation or drawer; right context panel on demand.
- Laptop/wide: full three-column chat with a 280px left and 320px right panel where space permits.
- Tables: preserve essential columns, collapse secondary metadata into row details.
- Maintain 44px targets, readable zoom, flexible text wrapping, and `min-width: 0` in flex/grid children.

Test at 320, 375, 480, 768, 1024, 1280, and 1440px plus browser zoom.
