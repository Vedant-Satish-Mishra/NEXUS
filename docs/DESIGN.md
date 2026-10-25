# NEXUS visual design brief

## Concept

NEXUS should feel like a focused personal intelligence workspace: a dark cocoa control room with warm cream work surfaces and visible evidence of the system’s reasoning process. It is not a generic SaaS dashboard or an opaque chatbot.

## Layout and hierarchy

Desktop chat uses three regions: 280px navigation/configuration sidebar, flexible conversation workspace, and roughly 320px agent/source context panel. The conversation and its next required user decision always dominate. At tablet width the right panel becomes a drawer; on phones the experience becomes one column with bottom sheets.

## Page character

- **Auth/onboarding:** quiet, reassuring, minimal choices.
- **Chat:** active, explainable, decision-focused.
- **Knowledge:** orderly document library with clear ingestion status.
- **Memory:** consent-first and easy to erase.
- **Workflows/tools:** operational clarity and approval safety.
- **Settings:** calm configuration, not a dense admin console.

## Design constraints

Use tokens from `DESIGN_SYSTEM.md`. Preserve whitespace, strong type hierarchy, one primary action per panel, and meaningful empty/error states. Avoid neon, gradients, ornamental cards, fake charts, dense icon-only controls, and decorative controls that look clickable.
