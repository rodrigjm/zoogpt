# Zoocari Web Frontend

React + TypeScript + Vite frontend for Zoocari voice-first zoo Q&A chatbot.

## Tech Stack

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite 6
- **Styling:** Tailwind CSS 3.4
- **State:** Zustand 5
- **Dev Server:** Vite dev server with HMR

## Getting Started

```bash
# Install dependencies
npm install

# Run development server (port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

## API Proxy

Vite proxies `/api/*` requests to `http://localhost:8000` (FastAPI backend).

## Project Structure

```
src/
├── types/           # TypeScript types matching CONTRACT.md
├── lib/             # API client (native fetch)
├── App.tsx          # Main app component
├── main.tsx         # React entry point
└── index.css        # Tailwind base styles
```

## Brand Colors

Defined in `tailwind.config.ts`:

- `leesburg-yellow`: #f5d224
- `leesburg-brown`: #3d332a
- `leesburg-beige`: #f4f2ef
- `leesburg-orange`: #f29021
- `leesburg-blue`: #76b9db

## Contract Alignment

All types in `src/types/index.ts` match `docs/integration/CONTRACT.md` Part 4.

API client in `src/lib/api.ts` provides typed wrappers for all endpoints.

## Status

Phase 0, Task 0.3 complete. Awaiting Phase 2 for component implementation.
