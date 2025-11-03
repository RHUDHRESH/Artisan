# Frontend Setup Guide

This frontend requires Next.js 14+ with TypeScript, Tailwind CSS, and shadcn/ui.

## Initial Setup

```bash
# Create Next.js app with TypeScript and Tailwind
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"

# Install shadcn/ui
npx shadcn-ui@latest init

# Install dependencies
npm install framer-motion usehooks-ts lucide-react

# Create component directory
mkdir -p components/ui
mkdir -p lib
```

## Required Dependencies

- next@14+
- react@18+
- typescript@5+
- tailwindcss@3+
- framer-motion@10+
- usehooks-ts@2.7+
- lucide-react@0.294+

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   └── ui/
│       ├── sidebar.tsx
│       ├── text-shimmer.tsx
│       └── expandable-tabs.tsx
├── lib/
│   └── utils.ts
└── package.json
```

## Next Steps

1. Copy the component files to `components/ui/`
2. Copy utils.ts if needed
3. Update the main page to use the new components



