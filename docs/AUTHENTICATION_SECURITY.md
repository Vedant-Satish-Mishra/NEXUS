# NEXUS authentication and security

## Required controls (proposed)

- Email/password authentication with slow password hashing; generic login failures; rate limits on login/register.
- Short-lived access token kept out of persistent browser storage where possible; refresh token in secure HttpOnly cookie with rotation/revocation strategy.
- Backend authorisation on every user-owned route. Return not-found rather than revealing another user’s resource.
- Input schemas at every boundary, output encoding, upload allow-list/content sniffing, size limits, and safe error messages.
- Secrets only in local environment/secret management, never source, screenshots, logs, or client bundles.
- Dependencies pinned and scanned; security headers, HTTPS for non-local deployment, CSRF strategy compatible with cookie flow.

## AI/tool-specific controls

Retrieved text is untrusted and cannot create tool calls. Validate structured tool calls against an allow-list and user/run scope. Python uses a separate non-root sandbox with no network, read-only base filesystem, resource limits, no Docker socket, and per-run approval. Never expose prompts, internal secrets, or chain-of-thought.

## Verification

Test cross-user access denial, token expiry/revocation, rate limiting, upload abuse, prompt injection fixtures, sandbox escape attempts, XSS/CSRF posture, and dependency alerts. No claim of security compliance is valid until these are tested.
