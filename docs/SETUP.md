# NEXUS setup

## Frontend application (`nexus frontend/`)

The frontend is a modern React + TypeScript single-page application built with Vite and Tailwind CSS / custom CSS variables, matching the approved design specifications and UI mockups.

### Prerequisites

- Node.js (v18+ recommended; v24 verified)
- npm (v9+ recommended; v11 verified)

### Quick start

```bash
# Navigate to the frontend directory
cd "nexus frontend"

# Install dependencies
npm install

# Run the development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Local architecture prerequisites (Full Stack)

- Windows host with Ollama and Qwen3 (4B default or 8B Q4)
- PostgreSQL database
- ChromaDB for vector retrieval
- Python FastAPI backend
- Docker for sandboxed code execution

## Safe setup rules

- Start from a committed `.env.example` containing names/descriptions only, never values.
- Put real secrets in untracked local `.env` files or an approved secret store.
- Verify service health, database migrations, model availability, and frontend/backend connectivity before feature work.
- Add real install/dev/test/build/troubleshooting commands here only after executing them successfully.
