"""
Search API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.scraping.search_engine import SearchEngine
from loguru import logger

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    region: str = "in"
    num_results: int = 10


@router.post("/web")
async def web_search(request: SearchRequest):
    """
    Perform web search
    """
    try:
        async with SearchEngine() as search_engine:
            results = await search_engine.search(
                query=request.query,
                region=request.region,
                num_results=request.num_results
            )
            
            return {
                "query": request.query,
                "region": request.region,
                "results": results,
                "count": len(results)
            }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

