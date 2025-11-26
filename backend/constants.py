"""
Application constants for Artisan Hub
Centralized configuration for models, timeouts, limits, and other magic values
"""

# ============================================================================
# LLM MODEL CONFIGURATION
# ============================================================================
EMBEDDING_MODEL_DEFAULT = "nomic-ai/nomic-embed-text-v1.5"
REASONING_MODEL_DEFAULT = "llama-3.3-70b-versatile"  # Groq default for complex reasoning
FAST_MODEL_DEFAULT = "llama-3.1-8b-instant"          # Groq default for fast responses
CHAT_MODEL = REASONING_MODEL_DEFAULT

# Cloud fallbacks
OPENROUTER_BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
OPENROUTER_REASONING_MODEL_DEFAULT = "openai/gpt-4o-mini"
OPENROUTER_FAST_MODEL_DEFAULT = "openai/gpt-4o-mini"
OPENROUTER_EMBEDDING_MODEL_DEFAULT = "text-embedding-3-large"
GEMINI_MODEL_DEFAULT = "gemini-1.5-flash"

# Legacy local defaults (kept for compatibility)
OLLAMA_REASONING_MODEL_DEFAULT = "gemma3:4b"
OLLAMA_FAST_MODEL_DEFAULT = "gemma3:1b"
OLLAMA_EMBEDDING_MODEL_DEFAULT = "nomic-embed-text:latest"

# ============================================================================
# API TIMEOUTS & RATE LIMITS (seconds)
# ============================================================================
TAVILY_API_TIMEOUT = 30
SERPAPI_TIMEOUT = 30
SCRAPING_TIMEOUT = 15
PLAYWRIGHT_TIMEOUT = 30000  # milliseconds
PLAYWRIGHT_WAIT_TIMEOUT = 2000  # milliseconds
WEBSOCKET_BROADCAST_TIMEOUT = 5

# ============================================================================
# VECTOR STORE CONFIGURATION
# ============================================================================
VECTOR_STORE_DEFAULT_PATH = "./data/chroma_db"
VECTOR_STORE_PERSIST_IMPL = "duckdb+parquet"

# Collections names
COLLECTION_CRAFT_KNOWLEDGE = "craft_knowledge"
COLLECTION_SUPPLIER_DATA = "supplier_data"
COLLECTION_MARKET_INSIGHTS = "market_insights"
COLLECTION_USER_CONTEXT = "user_context"
COLLECTION_ARTISAN_KNOWLEDGE = "artisan_knowledge"

# Vector query parameters
VECTOR_QUERY_DEFAULT_RESULTS = 5
VECTOR_MAX_RESULTS = 20
VECTOR_MIN_DISTANCE = 0.0
VECTOR_MAX_DISTANCE = 2.0

# ============================================================================
# WEB SCRAPING CONFIGURATION
# ============================================================================
SCRAPER_MAX_RESULTS = 10
SCRAPER_DEFAULT_REGION = "in"  # India
SCRAPER_SNIPPET_LENGTH = 200  # characters
SCRAPER_PAGE_CONTENT_LIMIT = 5000  # characters

# Scraper user agent
SCRAPER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ============================================================================
# SEARCH PROVIDER REGIONS
# ============================================================================
REGION_MAPPING = {
    "in": "India",
    "us": "United States",
    "uk": "United Kingdom",
    "au": "Australia"
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL_DEFAULT = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"

# ============================================================================
# HTTP RESPONSE CODES
# ============================================================================
HTTP_SUCCESS = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_INTERNAL_ERROR = 500

# ============================================================================
# BATCH PROCESSING CONFIGURATION
# ============================================================================
BATCH_SIZE_DEFAULT = 10
BATCH_MAX_SIZE = 100

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================
CACHE_DIR = "./data/cache"
CACHE_EXPIRY_SECONDS = 3600  # 1 hour

# ============================================================================
# WEBSOCKET CONFIGURATION
# ============================================================================
WEBSOCKET_MAX_CONNECTIONS = 1000
WEBSOCKET_HEARTBEAT_INTERVAL = 30  # seconds
WEBSOCKET_RECONNECT_TIMEOUT = 5  # seconds

# ============================================================================
# PAGINATION DEFAULTS
# ============================================================================
PAGINATION_DEFAULT_PAGE_SIZE = 20
PAGINATION_MAX_PAGE_SIZE = 100

# ============================================================================
# ERROR MESSAGE TEMPLATES
# ============================================================================
ERROR_INVALID_COLLECTION = "Invalid collection: {collection_name}"
ERROR_FAILED_TO_SCRAPE = "Failed to scrape {url}"
ERROR_VECTOR_STORE_INIT = "Could not initialize ChromaDB client in any mode"
ERROR_LLM_GENERATION = "Failed to generate response from LLM"
ERROR_SEARCH_FAILED = "Search operation failed"

# ============================================================================
# SUPPLY HUNTER CONSTANTS
# ============================================================================
SUPPLY_HUNTER_MAX_SUPPLIERS = 10
SUPPLY_HUNTER_CONFIDENCE_THRESHOLD = 0.6
SUPPLY_HUNTER_VERIFICATION_REQUIRED = True

# ============================================================================
# GROWTH MARKETER CONSTANTS
# ============================================================================
GROWTH_MARKETER_ANALYSIS_DEPTH = "detailed"
GROWTH_MARKETER_MAX_OPPORTUNITIES = 5

# ============================================================================
# EVENT SCOUT CONSTANTS
# ============================================================================
EVENT_SCOUT_MAX_EVENTS = 10
EVENT_SCOUT_DAYS_LOOKAHEAD = 90

# ============================================================================
# PROFILE ANALYST CONSTANTS
# ============================================================================
PROFILE_ANALYST_EXTRACTION_MODEL = "gemma3:4b"
PROFILE_ANALYST_MIN_CONFIDENCE = 0.7

# ============================================================================
# VALIDATION CONSTRAINTS
# ============================================================================
MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 500
MIN_PROFILE_NAME_LENGTH = 2
MAX_PROFILE_NAME_LENGTH = 100

# ============================================================================
# ASYNC WORKER CONFIGURATION
# ============================================================================
MAX_CONCURRENT_SCRAPING_TASKS = 5
MAX_CONCURRENT_API_CALLS = 10
WORKER_TIMEOUT = 60  # seconds
