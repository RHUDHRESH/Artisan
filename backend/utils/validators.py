"""
Input validators for API endpoints
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, validator
from loguru import logger


class LocationValidator:
    """Validate location data"""
    
    @staticmethod
    def validate(location: Dict) -> bool:
        """Validate location dictionary"""
        if not isinstance(location, dict):
            return False
        
        # Must have at least city or coordinates
        has_city = bool(location.get("city"))
        has_coords = bool(location.get("lat") and location.get("lon"))
        
        return has_city or has_coords
    
    @staticmethod
    def normalize(location: Dict) -> Dict:
        """Normalize location data"""
        normalized = location.copy()
        
        # Ensure country defaults to India
        if not normalized.get("country"):
            normalized["country"] = "India"
        
        # Ensure coordinates are floats if present
        if "lat" in normalized:
            try:
                normalized["lat"] = float(normalized["lat"])
            except (ValueError, TypeError):
                normalized.pop("lat", None)
        
        if "lon" in normalized:
            try:
                normalized["lon"] = float(normalized["lon"])
            except (ValueError, TypeError):
                normalized.pop("lon", None)
        
        return normalized


class CraftTypeValidator:
    """Validate craft type"""
    
    VALID_CRAFT_TYPES = [
        "pottery", "weaving", "metalwork", "woodwork", "textile", "jewelry",
        "painting", "sculpture", "embroidery", "leatherwork", "basketwork"
    ]
    
    @classmethod
    def validate(cls, craft_type: str) -> bool:
        """Check if craft type is valid"""
        if not craft_type:
            return False
        
        craft_lower = craft_type.lower()
        
        # Exact match
        if craft_lower in cls.VALID_CRAFT_TYPES:
            return True
        
        # Partial match
        for valid_craft in cls.VALID_CRAFT_TYPES:
            if valid_craft in craft_lower or craft_lower in valid_craft:
                return True
        
        return False
    
    @classmethod
    def normalize(cls, craft_type: str) -> str:
        """Normalize craft type to standard form"""
        if not craft_type:
            return "unknown"
        
        craft_lower = craft_type.lower()
        
        # Try to find matching valid type
        for valid_craft in cls.VALID_CRAFT_TYPES:
            if valid_craft in craft_lower:
                return valid_craft
        
        return craft_lower


class SupplyListValidator:
    """Validate supplies list"""
    
    @staticmethod
    def validate(supplies: List[str]) -> bool:
        """Validate supplies list"""
        if not isinstance(supplies, list):
            return False
        
        if len(supplies) == 0:
            return False
        
        # All items must be non-empty strings
        return all(isinstance(s, str) and len(s.strip()) > 0 for s in supplies)
    
    @staticmethod
    def normalize(supplies: List[str]) -> List[str]:
        """Normalize supplies list"""
        if not isinstance(supplies, list):
            return []
        
        # Filter and strip
        normalized = [s.strip() for s in supplies if isinstance(s, str) and s.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for supply in normalized:
            supply_lower = supply.lower()
            if supply_lower not in seen:
                seen.add(supply_lower)
                unique.append(supply)
        
        return unique


class UserProfileValidator:
    """Validate user profile data"""
    
    @staticmethod
    def validate(profile: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate user profile
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not profile.get("craft_type") and not profile.get("input_text"):
            return False, "Must provide either craft_type or input_text"
        
        # Validate location if provided
        if "location" in profile:
            if not LocationValidator.validate(profile["location"]):
                return False, "Invalid location data"
        
        # Validate craft type if provided
        if profile.get("craft_type"):
            if not CraftTypeValidator.validate(profile["craft_type"]):
                return False, f"Invalid craft type: {profile['craft_type']}"
        
        # Validate supplies if provided
        if "supplies_needed" in profile:
            if not SupplyListValidator.validate(profile["supplies_needed"]):
                return False, "Invalid supplies list"
        
        return True, None
    
    @staticmethod
    def normalize(profile: Dict) -> Dict:
        """Normalize user profile data"""
        normalized = profile.copy()
        
        # Normalize craft type
        if normalized.get("craft_type"):
            normalized["craft_type"] = CraftTypeValidator.normalize(normalized["craft_type"])
        
        # Normalize location
        if normalized.get("location"):
            normalized["location"] = LocationValidator.normalize(normalized["location"])
        
        # Normalize supplies
        if normalized.get("supplies_needed"):
            normalized["supplies_needed"] = SupplyListValidator.normalize(normalized["supplies_needed"])
        
        return normalized


# Pydantic models with validation
class ValidatedLocation(BaseModel):
    """Validated location model"""
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    lat: Optional[float] = None
    lon: Optional[float] = None
    
    @validator('country')
    def country_default(cls, v):
        return v or "India"
    
    class Config:
        extra = "allow"


class ValidatedCraftProfile(BaseModel):
    """Validated craft profile model"""
    craft_type: Optional[str] = None
    specialization: Optional[str] = None
    location: Optional[ValidatedLocation] = None
    supplies_needed: Optional[List[str]] = []
    
    @validator('craft_type')
    def validate_craft_type(cls, v):
        if v and not CraftTypeValidator.validate(v):
            raise ValueError(f"Invalid craft type: {v}")
        return v
    
    @validator('supplies_needed')
    def validate_supplies(cls, v):
        if v and not SupplyListValidator.validate(v):
            raise ValueError("Invalid supplies list")
        return SupplyListValidator.normalize(v) if v else []

