# NEXUS UI/UX guidelines

## Do

- Place the next required decision adjacent to its context: plan approval beside the plan, Python approval beside the code.
- Use one primary CTA per bounded panel.
- Make source, agent, run, and approval states readable in text—not colour alone.
- Use concise labels: “Approve plan”, “Re-plan”, “Run”, “Deny”, “Retry”.
- Keep data tables scannable with stable columns, filters, and empty states.

## Do not

- Put every group inside a card, use gradients as decoration, or show unrequested animation.
- Hide destructive actions without confirmation or make dangerous and safe actions visually identical.
- Use a toggle for actions that require immediate explicit approval.

## Interaction baseline

Links navigate; buttons act; icon-only controls have accessible names/tooltips; dialogs trap focus and restore it on close. Forms validate near the field and preserve entered values after a recoverable failure. Keyboard users can reach all controls in visual order.
