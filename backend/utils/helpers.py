"""
Utility helper functions
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from loguru import logger


def clean_json_response(text: str) -> str:
    """
    Clean JSON response from LLM, removing markdown code blocks
    
    Args:
        text: Raw LLM response
    
    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        # Try to extract JSON from code block
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("{") or part.startswith("["):
                text = part
                break
    
    return text.strip()


def safe_json_parse(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON from LLM response
    
    Args:
        text: Text to parse
        default: Default value if parsing fails
    
    Returns:
        Parsed JSON object or default
    """
    try:
        cleaned = clean_json_response(text)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}\nText: {text[:200]}")
        return default


def format_currency(amount: float, currency: str = "Rs") -> str:
    """
    Format currency amount for display
    
    Args:
        amount: Amount to format
        currency: Currency symbol
    
    Returns:
        Formatted string
    """
    if amount >= 100000:
        return f"{currency} {amount/100000:.1f}L"
    elif amount >= 1000:
        return f"{currency} {amount/1000:.1f}K"
    else:
        return f"{currency} {amount:.0f}"


def calculate_confidence_score(factors: Dict[str, float]) -> float:
    """
    Calculate confidence score from multiple factors
    
    Args:
        factors: Dictionary of factor_name -> weight
    
    Returns:
        Confidence score between 0 and 1
    """
    total = sum(factors.values())
    return min(1.0, max(0.0, total))


def deduplicate_list(items: List[Dict], key_func) -> List[Dict]:
    """
    Deduplicate list of dictionaries based on a key function
    
    Args:
        items: List of dictionaries
        key_func: Function to extract key from item
    
    Returns:
        Deduplicated list
    """
    seen = set()
    unique = []
    
    for item in items:
        key = key_func(item)
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    
    return unique


def extract_location_string(location: Dict) -> str:
    """
    Extract location string from location dictionary
    
    Args:
        location: Location dictionary
    
    Returns:
        Formatted location string
    """
    parts = []
    if location.get("city"):
        parts.append(location["city"])
    if location.get("state"):
        parts.append(location["state"])
    if location.get("country"):
        parts.append(location["country"])
    elif not parts:
        parts.append("India")  # Default
    
    return ", ".join(parts)


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """
    Sanitize and truncate text
    
    Args:
        text: Text to sanitize
        max_length: Maximum length
    
    Returns:
        Sanitized text
    """
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format
    
    Returns:
        ISO format timestamp string
    """
    return datetime.now().isoformat()


def validate_location(location: Dict) -> bool:
    """
    Validate location dictionary has required fields
    
    Args:
        location: Location dictionary
    
    Returns:
        True if valid, False otherwise
    """
    return isinstance(location, dict) and (
        location.get("city") or 
        location.get("state") or 
        location.get("country") or
        (location.get("lat") and location.get("lon"))
    )


def format_agent_result(result: Dict, agent_name: str) -> str:
    """
    Format agent result for display
    
    Args:
        result: Agent result dictionary
        agent_name: Name of the agent
    
    Returns:
        Formatted string
    """
    lines = [f"=== {agent_name} Results ==="]
    
    if "craft_type" in result:
        lines.append(f"Craft: {result['craft_type']}")
    
    if "location" in result:
        loc = result["location"]
        lines.append(f"Location: {extract_location_string(loc)}")
    
    if "suppliers" in result:
        lines.append(f"Suppliers Found: {result.get('total_suppliers_found', 0)}")
    
    if "trends" in result:
        lines.append(f"Trends Found: {len(result.get('trends', []))}")
    
    if "upcoming_events" in result:
        lines.append(f"Events Found: {result.get('total_events_found', 0)}")
    
    return "\n".join(lines)

