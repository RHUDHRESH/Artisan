# Artisan Hub - Agent Specifications

## Overview

Artisan Hub uses a multi-agent system where specialized AI agents work together to help artisans. Each agent has specific responsibilities and uses appropriate Gemma 3 models.

## Agent Architecture

### Base Agent Class

All agents inherit from `BaseAgent` which provides:
- Execution logging
- Audit trail support
- Timestamp tracking
- Common interface (`analyze()` method)

## Agents

### 1. Profile Analyst Agent

**Purpose:** Parse unstructured user input and extract artisan profile information.

**Model Used:** Gemma 3 4B (reasoning model)

**Responsibilities:**
- Extract craft type and specialization
- Identify location
- Infer tools, supplies, and skills needed
- Determine workspace requirements
- Identify skill adjacencies
- Assess market positioning

**Input Format:**
```json
{
  "input_text": "I'm Raj, I make blue pottery in Jaipur...",
  "user_id": "optional"
}
```

**Output Format:**
```json
{
  "craft_type": "pottery",
  "specialization": "blue pottery",
  "location": {...},
  "inferred_needs": {...},
  "skill_adjacencies": [...],
  "confidence": 0.85
}
```

---

### 2. Supply Hunter Agent

**Purpose:** Find and verify suppliers for artisan materials.

**Model Used:** Gemma 3 4B (for analysis), 1B (for classification)

**Responsibilities:**
- Search for suppliers (India-first)
- Scrape supplier websites
- Verify supplier legitimacy
- Calculate confidence scores
- Maintain detailed search logs

**Search Priority:**
1. India (mandatory first)
2. Regional (Asia) if needed
3. Global only if unavailable

**Input Format:**
```json
{
  "craft_type": "pottery",
  "supplies_needed": ["clay", "glazes"],
  "location": {...}
}
```

**Output Format:**
```json
{
  "suppliers": [...],
  "total_suppliers_found": 5,
  "india_suppliers": 4,
  "search_logs": [...]
}
```

---

### 3. Growth Marketer Agent

**Purpose:** Identify growth opportunities and market trends.

**Model Used:** Gemma 3 4B

**Responsibilities:**
- Research market trends
- Generate product innovation ideas
- Analyze pricing strategies
- Calculate ROI projections
- Identify marketing channels

**Input Format:**
```json
{
  "craft_type": "pottery",
  "specialization": "blue pottery",
  "current_products": [...],
  "location": {...}
}
```

**Output Format:**
```json
{
  "trends": [...],
  "product_innovations": [...],
  "pricing_insights": {...},
  "roi_projections": [...],
  "marketing_channels": [...]
}
```

---

### 4. Event Scout Agent

**Purpose:** Find relevant events and opportunities.

**Model Used:** Gemma 3 4B (for matching and analysis)

**Responsibilities:**
- Find craft fairs and exhibitions
- Discover government schemes
- Identify workshop opportunities
- Calculate event ROI
- Match events to location

**Input Format:**
```json
{
  "craft_type": "pottery",
  "location": {...},
  "travel_radius_km": 100
}
```

**Output Format:**
```json
{
  "upcoming_events": [...],
  "government_schemes": [...],
  "workshop_opportunities": [...],
  "total_events_found": 12
}
```

---

## Agent Workflow

1. **User Input** → Profile Analyst extracts profile
2. **Profile Data** → Supply Hunter finds suppliers
3. **Profile Data** → Growth Marketer analyzes opportunities
4. **Profile Data** → Event Scout finds events

All agents store results in ChromaDB for future reference.

---

## Model Selection

- **Gemma 3 4B:** Complex reasoning, analysis, planning, extraction
- **Gemma 3 1B:** Fast responses, classifications, simple routing
- **Gemma 3 Embed:** All embeddings for vector search

---

## Audit Trails

All agents maintain complete execution logs:
- Timestamp for each step
- Input/output data
- Confidence scores
- Error messages

Access logs via `execution_logs` field in agent responses.

---

## Confidence Scoring

All agents return confidence scores (0.0 - 1.0):
- 0.9+ : Very High Confidence
- 0.7-0.9 : High Confidence
- 0.5-0.7 : Medium Confidence
- <0.5 : Low Confidence

---

## Best Practices

1. Always validate input data before passing to agents
2. Check confidence scores before trusting results
3. Review execution logs for debugging
4. Use India-first approach for all searches
5. Verify all scraped data with confidence > 0.6

