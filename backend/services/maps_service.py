"""
Maps Service - Geolocation and distance calculations
"""
from typing import Dict, Optional, Tuple
from loguru import logger
from geopy.distance import distance as geopy_distance
from geopy.geocoders import Nominatim
import asyncio


class MapsService:
    """
    Maps Service for geolocation and distance calculations
    Uses Geopy for geocoding and distance calculations
    """
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="artisan-hub")
        # Cache for geocoding results
        self.geocache: Dict[str, Tuple[float, float]] = {}
    
    async def geocode(self, location_text: str) -> Optional[Dict[str, float]]:
        """
        Geocode a location string to coordinates
        
        Args:
            location_text: Location string (e.g., "Jaipur, Rajasthan, India")
        
        Returns:
            Dict with 'lat' and 'lon' or None
        """
        # Check cache first
        if location_text in self.geocache:
            lat, lon = self.geocache[location_text]
            return {"lat": lat, "lon": lon}
        
        try:
            # Run geocoding in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            location = await loop.run_in_executor(
                None,
                self.geolocator.geocode,
                location_text,
                10  # timeout
            )
            
            if location:
                result = {
                    "lat": location.latitude,
                    "lon": location.longitude
                }
                # Cache result
                self.geocache[location_text] = (location.latitude, location.longitude)
                return result
            else:
                logger.warning(f"Could not geocode: {location_text}")
                return None
        except Exception as e:
            logger.error(f"Geocoding error for {location_text}: {e}")
            return None
    
    async def calculate_distance(
        self,
        location1: Dict,
        location2: Dict
    ) -> float:
        """
        Calculate distance between two locations in kilometers
        
        Args:
            location1: Dict with 'lat' and 'lon' or location string
            location2: Dict with 'lat' and 'lon' or location string
        
        Returns:
            Distance in kilometers
        """
        try:
            # Get coordinates for both locations
            coords1 = await self._get_coordinates(location1)
            coords2 = await self._get_coordinates(location2)
            
            if not coords1 or not coords2:
                # Fallback: estimate based on city names
                return self._estimate_distance(location1, location2)
            
            # Calculate distance using geopy
            dist = geopy_distance(coords1, coords2)
            return round(dist.kilometers, 2)
        
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return self._estimate_distance(location1, location2)
    
    async def _get_coordinates(self, location: Dict) -> Optional[Tuple[float, float]]:
        """Get coordinates from location dict"""
        if isinstance(location, dict):
            if "lat" in location and "lon" in location:
                return (location["lat"], location["lon"])
            elif "city" in location:
                # Build location string
                parts = []
                if "city" in location:
                    parts.append(location["city"])
                if "state" in location:
                    parts.append(location["state"])
                if "country" in location:
                    parts.append(location["country"])
                elif not parts:
                    parts.append("India")  # Default
                
                location_str = ", ".join(parts)
                result = await self.geocode(location_str)
                if result:
                    return (result["lat"], result["lon"])
        
        return None
    
    def _estimate_distance(self, location1: Dict, location2: Dict) -> float:
        """Estimate distance based on city names (fallback)"""
        city1 = location1.get("city", "").lower() if isinstance(location1, dict) else ""
        city2 = location2.get("city", "").lower() if isinstance(location2, dict) else ""
        
        if city1 == city2:
            return 5.0  # Same city, assume 5km
        
        # Same state
        state1 = location1.get("state", "").lower() if isinstance(location1, dict) else ""
        state2 = location2.get("state", "").lower() if isinstance(location2, dict) else ""
        
        if state1 == state2 and state1:
            return 50.0  # Same state, estimate 50km
        
        # Different states
        return 500.0  # Different states, estimate 500km


# Test the Maps Service
async def test_maps_service():
    service = MapsService()
    
    # Test geocoding
    print("Testing geocoding...")
    result = await service.geocode("Jaipur, Rajasthan, India")
    if result:
        print(f"Jaipur coordinates: {result}")
    
    # Test distance calculation
    print("\nTesting distance calculation...")
    dist = await service.calculate_distance(
        {"city": "Jaipur", "state": "Rajasthan"},
        {"city": "Delhi", "state": "Delhi"}
    )
    print(f"Jaipur to Delhi: {dist} km")
    
    # Test with coordinates
    dist2 = await service.calculate_distance(
        {"lat": 26.9124, "lon": 75.7873},  # Jaipur
        {"lat": 28.7041, "lon": 77.1025}   # Delhi
    )
    print(f"Jaipur to Delhi (coordinates): {dist2} km")


if __name__ == "__main__":
    asyncio.run(test_maps_service())
