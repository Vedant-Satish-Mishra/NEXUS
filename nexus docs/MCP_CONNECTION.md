# Model Context Protocol (MCP) connection

No product requirement establishes a Model Context Protocol integration for NEXUS v1. Do not add an MCP server, endpoint, tool, or credential by assumption.

If a later approved feature needs MCP, create a separate design covering the server purpose, explicit user permissions, least-privilege tools, environment-variable names (not values), startup, audit trail, timeout/failure behaviour, data egress, and disable/remove path. Untrusted MCP tools must not receive user documents or secrets by default.
