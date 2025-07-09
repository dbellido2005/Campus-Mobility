"""
Google Routes API Integration for Campus Mobility
Provides detailed route information including distance, duration, and route geometry
"""

import os
import aiohttp
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleRoutesService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_ROUTES_API_KEY')
        self.base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        
    async def get_route_info(
        self, 
        origin_lat: float, 
        origin_lng: float, 
        destination_lat: float, 
        destination_lng: float,
        travel_mode: str = "DRIVE",
        departure_time: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Get detailed route information from Google Routes API
        Returns distance, duration, and route geometry
        """
        
        if not self.api_key:
            logger.warning("Google Routes API key not configured")
            return None
            
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline,routes.legs'
            }
            
            payload = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": origin_lat,
                            "longitude": origin_lng
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": destination_lat,
                            "longitude": destination_lng
                        }
                    }
                },
                "travelMode": travel_mode,
                "polylineQuality": "OVERVIEW",
                "routingPreference": "TRAFFIC_AWARE"
            }
            
            # Add departure time if provided
            if departure_time:
                payload["departureTime"] = departure_time.isoformat()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, 
                    headers=headers, 
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_routes_response(data)
                    else:
                        logger.warning(f"Google Routes API request failed with status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error response: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Google Routes API: {str(e)}")
            return None

    def _parse_routes_response(self, data: Dict) -> Optional[Dict]:
        """Parse Google Routes API response and format for frontend"""
        
        routes = data.get('routes', [])
        if not routes:
            return None
            
        # Get the first (best) route
        route = routes[0]
        
        # Extract basic route info
        duration = route.get('duration', '0s')
        distance_meters = route.get('distanceMeters', 0)
        polyline = route.get('polyline', {}).get('encodedPolyline', '')
        
        # Parse duration (format: "1234s" -> seconds)
        duration_seconds = int(duration.rstrip('s')) if duration.endswith('s') else 0
        duration_minutes = duration_seconds / 60
        
        # Convert distance to miles
        distance_miles = distance_meters * 0.000621371
        
        # Format duration for display
        formatted_duration = self._format_duration(duration_minutes)
        
        # Get detailed leg information if available
        legs = route.get('legs', [])
        leg_details = []
        
        for leg in legs:
            leg_info = {
                'duration': leg.get('duration', '0s'),
                'distance_meters': leg.get('distanceMeters', 0),
                'start_location': leg.get('startLocation', {}),
                'end_location': leg.get('endLocation', {})
            }
            leg_details.append(leg_info)
        
        return {
            'distance_meters': distance_meters,
            'distance_miles': distance_miles,
            'formatted_distance': f"{distance_miles:.1f} miles",
            'duration_seconds': duration_seconds,
            'duration_minutes': duration_minutes,
            'formatted_duration': formatted_duration,
            'polyline': polyline,
            'legs': leg_details,
            'source': 'google_routes_api'
        }

    def _format_duration(self, minutes: float) -> str:
        """Format duration in minutes to human-readable string"""
        if minutes < 60:
            return f"{int(minutes)} min"
        else:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            if mins == 0:
                return f"{hours} hr"
            else:
                return f"{hours} hr {mins} min"

    async def get_route_matrix(
        self, 
        origins: List[Dict[str, float]], 
        destinations: List[Dict[str, float]]
    ) -> Optional[Dict]:
        """
        Get route matrix for multiple origins and destinations
        Each origin/destination should be {'lat': float, 'lng': float}
        """
        
        if not self.api_key:
            logger.warning("Google Routes API key not configured")
            return None
            
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters'
            }
            
            # Convert origins and destinations to API format
            formatted_origins = []
            for origin in origins:
                formatted_origins.append({
                    "location": {
                        "latLng": {
                            "latitude": origin['lat'],
                            "longitude": origin['lng']
                        }
                    }
                })
            
            formatted_destinations = []
            for dest in destinations:
                formatted_destinations.append({
                    "location": {
                        "latLng": {
                            "latitude": dest['lat'],
                            "longitude": dest['lng']
                        }
                    }
                })
            
            payload = {
                "origins": formatted_origins,
                "destinations": formatted_destinations,
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_AWARE"
            }
            
            # Use the compute route matrix endpoint
            matrix_url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    matrix_url, 
                    headers=headers, 
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_matrix_response(data)
                    else:
                        logger.warning(f"Google Routes Matrix API request failed with status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error response: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Google Routes Matrix API: {str(e)}")
            return None

    def _parse_matrix_response(self, data: Dict) -> Optional[Dict]:
        """Parse Google Routes Matrix API response"""
        # This would be implemented based on the actual matrix API response structure
        # For now, return a basic structure
        return {
            'matrix': data,
            'source': 'google_routes_matrix_api'
        }

# Global instance
google_routes_service = GoogleRoutesService()