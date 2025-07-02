# routes/places.py
import httpx
import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status

# Load environment variables
load_dotenv()
from models import (
    PlaceAutocompleteRequest, 
    PlaceAutocompleteResponse, 
    PlaceSuggestion,
    PlaceDetailsRequest,
    PlaceDetailsResponse,
    PlaceLocation
)

router = APIRouter()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

@router.post("/places/autocomplete", response_model=PlaceAutocompleteResponse)
async def get_place_autocomplete(request: PlaceAutocompleteRequest):
    """Get place autocomplete suggestions from Google Places API"""
    
    if not GOOGLE_PLACES_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Places API key not configured"
        )
    
    if len(request.query) < 2:
        return PlaceAutocompleteResponse(suggestions=[])
    
    try:
        async with httpx.AsyncClient() as client:
            url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
            params = {
                "input": request.query,
                "key": GOOGLE_PLACES_API_KEY,
                "types": "establishment|geocode",
                "components": "country:us"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("predictions"):
                suggestions = [
                    PlaceSuggestion(
                        place_id=prediction["place_id"],
                        description=prediction["description"]
                    )
                    for prediction in data["predictions"]
                ]
                return PlaceAutocompleteResponse(suggestions=suggestions)
            else:
                return PlaceAutocompleteResponse(suggestions=[])
                
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Places API error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Google Places API"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching place suggestions"
        )

@router.post("/places/details", response_model=PlaceDetailsResponse)
async def get_place_details(request: PlaceDetailsRequest):
    """Get detailed place information including coordinates from Google Places API"""
    
    if not GOOGLE_PLACES_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Places API key not configured"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": request.place_id,
                "fields": "geometry,name,formatted_address",
                "key": GOOGLE_PLACES_API_KEY
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("result"):
                result = data["result"]
                location = None
                
                if result.get("geometry") and result["geometry"].get("location"):
                    location = PlaceLocation(
                        latitude=result["geometry"]["location"]["lat"],
                        longitude=result["geometry"]["location"]["lng"]
                    )
                
                return PlaceDetailsResponse(
                    name=result.get("name", ""),
                    description=result.get("formatted_address", ""),
                    location=location
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Place not found"
                )
                
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Places API error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Google Places API"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching place details"
        )