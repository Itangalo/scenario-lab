# Scenario Lab - React Frontend

React + TypeScript + TailwindCSS frontend for Scenario Lab's human-in-the-loop interface.

## Overview

This frontend provides a web interface for human actors to participate in AI-powered scenario simulations in real-time.

## Features

- Real-time scenario monitoring dashboard
- Actor status tracking (AI and human)
- Human decision input forms
- WebSocket-based live updates
- Turn progress and cost tracking
- Responsive design with TailwindCSS

## Technology Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS 4** - Styling
- **WebSocket** - Real-time communication

## Development

```bash
# Install dependencies
npm install

# Start development server (with Vite proxy to backend)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ScenarioDashboard.tsx    # Real-time status dashboard
│   │   └── HumanActorInterface.tsx  # Decision input form
│   ├── App.tsx                       # Main application
│   ├── main.tsx                      # Entry point
│   ├── types.ts                      # TypeScript definitions
│   └── index.css                     # Global styles
├── index.html                        # HTML template
├── vite.config.ts                    # Vite configuration
├── tailwind.config.js                # TailwindCSS configuration
├── postcss.config.js                 # PostCSS configuration
└── tsconfig.json                     # TypeScript configuration
```

## Components

### ScenarioDashboard

Displays real-time scenario status:
- Current turn number
- Total cost tracker
- Actor status grid (waiting, thinking, complete, your turn)
- Recent activity feed
- Pause indicators

### HumanActorInterface

Human decision input form:
- Long-term goals (dynamic list)
- Short-term priorities (dynamic list)
- Reasoning textarea
- Action textarea
- Form validation
- Submit to backend API

## API Integration

The frontend connects to the FastAPI backend:

- `GET /api/status` - Fetch current scenario status
- `POST /api/human/decision` - Submit human decision
- `WebSocket /ws` - Real-time updates

## Build Output

Build artifacts are generated in `../static/` directory:
- `index.html` - Entry HTML
- `assets/` - JS and CSS bundles

The FastAPI backend serves these files directly.

## Phase 3 Completion

This frontend completes **Phase 3: Human Interaction** from the Scenario Lab roadmap:

- Human Actor Interface (web UI)
- Real-time Scenario Dashboard
- WebSocket integration for live updates
- Decision submission and validation
