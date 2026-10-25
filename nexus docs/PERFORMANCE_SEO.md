# NEXUS performance and SEO

NEXUS is primarily an authenticated local application; public-page SEO applies only to an eventual landing page, not private chat/documents.

## Performance requirements

- Measure first token time, streaming responsiveness, route load time, interaction responsiveness, layout shift, memory, and VRAM on the target laptop.
- Lazy-load non-critical routes/graphs, virtualise long lists, use responsive compressed assets, reserve image dimensions, and subset/preload fonts only after measurement.
- Avoid blocking animations, duplicate LLM calls, unbounded context, and client bundles that include backend-only libraries.

## Public metadata (if a public landing page is approved)

Provide unique title/description, canonical URL, social preview, semantic content, sitemap/robots rules, and only truthful structured data. Exclude authenticated/private routes from indexing and never expose documents, chats, or memories. Do not promise rankings.
