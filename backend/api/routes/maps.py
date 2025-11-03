"""
Map API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.services.maps_service import MapsService
from loguru import logger

router = APIRouter(prefix="/maps", tags=["maps"])


class GeocodeRequest(BaseModel):
    location_text: str


class DistanceRequest(BaseModel):
    location1: Dict[str, Any]
    location2: Dict[str, Any]


@router.post("/geocode")
async def geocode_location(request: GeocodeRequest):
    """
    Geocode a location string to coordinates
    """
    try:
        maps = MapsService()
        result = await maps.geocode(request.location_text)
        
        if result:
            return {
                "success": True,
                "location": request.location_text,
                "coordinates": result
            }
        else:
            return {
                "success": False,
                "message": "Could not geocode location"
            }
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/distance")
async def calculate_distance(request: DistanceRequest):
    """
    Calculate distance between two locations
    """
    try:
        maps = MapsService()
        distance = await maps.calculate_distance(
            request.location1,
            request.location2
        )
        
        return {
            "location1": request.location1,
            "location2": request.location2,
            "distance_km": distance
        }
    except Exception as e:
        logger.error(f"Distance calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

