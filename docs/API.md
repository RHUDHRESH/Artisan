# Artisan Hub - API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required. All endpoints are open.

## Endpoints

### Health Check

#### `GET /health`
Check API health and Ollama connection status.

**Response:**
```json
{
  "status": "healthy",
  "message": "Ollama connected",
  "ollama_connected": true
}
```

---

### Chat

#### `POST /chat/send`
Send a message to the AI assistant.

**Request:**
```json
{
  "message": "I make blue pottery in Jaipur",
  "conversation_history": [],
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "response": "Hello! I'd be happy to help you with your blue pottery business...",
  "model_used": "gemma3:4b",
  "processing_time": 2.34
}
```

---

### Agents

#### `POST /agents/profile/analyze`
Analyze artisan profile from unstructured text.

**Request:**
```json
{
  "input_text": "I'm Raj, I make traditional blue pottery in Jaipur...",
  "user_id": "user_001"
}
```

**Response:**
```json
{
  "craft_type": "pottery",
  "specialization": "blue pottery",
  "location": {
    "city": "Jaipur",
    "state": "Rajasthan",
    "country": "India"
  },
  "inferred_needs": {
    "tools": ["pottery wheel", "kiln", "glazing tools"],
    "supplies": ["clay", "blue pigments", "glazes"],
    "skills": ["wheel throwing", "glazing"]
  },
  "execution_logs": [...]
}
```

#### `POST /agents/supply/search`
Search for suppliers.

**Request:**
```json
{
  "craft_type": "pottery",
  "supplies_needed": ["clay", "glazes"],
  "location": {
    "city": "Jaipur",
    "state": "Rajasthan"
  }
}
```

**Response:**
```json
{
  "suppliers": [
    {
      "name": "Supplier Name",
      "products": ["clay", "glazes"],
      "location": {"city": "Jaipur"},
      "verification": {
        "confidence": 0.85,
        "legitimacy_indicators": ["Phone number provided", "Website available"]
      }
    }
  ],
  "total_suppliers_found": 5,
  "india_suppliers": 4
}
```

#### `POST /agents/growth/analyze`
Analyze growth opportunities.

**Request:**
```json
{
  "craft_type": "pottery",
  "specialization": "blue pottery",
  "current_products": ["plates", "vases"],
  "location": {"city": "Jaipur", "state": "Rajasthan"}
}
```

#### `POST /agents/events/search`
Search for events and opportunities.

**Request:**
```json
{
  "craft_type": "pottery",
  "location": {"city": "Jaipur", "state": "Rajasthan"},
  "travel_radius_km": 100
}
```

---

### Maps

#### `POST /maps/geocode`
Geocode a location string to coordinates.

**Request:**
```json
{
  "location_text": "Jaipur, Rajasthan, India"
}
```

**Response:**
```json
{
  "success": true,
  "location": "Jaipur, Rajasthan, India",
  "coordinates": {
    "lat": 26.9124,
    "lon": 75.7873
  }
}
```

#### `POST /maps/distance`
Calculate distance between two locations.

**Request:**
```json
{
  "location1": {"city": "Jaipur"},
  "location2": {"city": "Delhi"}
}
```

---

### Search

#### `POST /search/web`
Perform web search.

**Request:**
```json
{
  "query": "pottery suppliers Jaipur",
  "region": "in",
  "num_results": 10
}
```

---

### WebSocket

#### `WS /ws`
WebSocket endpoint for real-time updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Message Types:**
- `agent_progress` - Agent execution updates
- `search_complete` - Search completion notifications

---

## Error Responses

All errors return standard HTTP status codes:

- `400` - Bad Request
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message here"
}
```

---

## Rate Limiting

Currently no rate limiting. Consider implementing for production use.

---

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

