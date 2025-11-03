# Artisan Hub Frontend

Next.js 14+ frontend with React, TypeScript, Tailwind CSS, and shadcn/ui.

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Visit: http://localhost:3000

## Features

1. **8 Questions Questionnaire** - Black and white dialogue box to collect initial user information
2. **Production Gate System** - Main dashboard with sidebar menu (3 horizontal lines hamburger)
3. **Real-time AI Thinking** - Shows what AI agents are searching and thinking
4. **Sidebar Navigation** - Access to:
   - Dashboard
   - Suppliers
   - Opportunities
   - Growth Marketer
   - Events
   - Materials & Equipment
   - Context
   - Settings

## Components

- `components/questionnaire.tsx` - 8 questions dialogue
- `components/production-gate.tsx` - Main production gate system
- `components/ai-thinking.tsx` - Real-time AI activity display
- `components/ui/sidebar.tsx` - Sidebar component
- `components/ui/text-shimmer.tsx` - Shimmer text animation
- `components/ui/expandable-tabs.tsx` - Expandable tabs component

## Backend Connection

Frontend connects to backend at: `http://localhost:8000`
WebSocket for real-time updates: `ws://localhost:8000/ws`
