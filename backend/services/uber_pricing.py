"""
Uber Sandbox API Integration for Campus Mobility
Simple implementation that only uses Uber API - no fallback pricing
"""

import os
import aiohttp
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class UberPricingService:
    def __init__(self):
        self.uber_server_token = os.getenv('UBER_SERVER_TOKEN')
        self.uber_sandbox_mode = os.getenv('UBER_SANDBOX_MODE', 'true').lower() == 'true'
        
        # Uber API endpoints
        self.uber_base_url = "https://sandbox-api.uber.com" if self.uber_sandbox_mode else "https://api.uber.com"

    async def get_price_estimate(
        self, 
        start_lat: float, 
        start_lng: float, 
        end_lat: float, 
        end_lng: float,
        product_type: str = "uberX"
    ) -> Optional[Dict]:
        """
        Get price estimate from Uber API only
        Returns None if API is unavailable or fails
        """
        
        if not self.uber_server_token:
            logger.warning("Uber API token not configured")
            return None
            
        try:
            headers = {
                'Authorization': f'Token {self.uber_server_token}',
                'Accept-Language': 'en_US',
                'Content-Type': 'application/json'
            }
            
            params = {
                'start_latitude': start_lat,
                'start_longitude': start_lng,
                'end_latitude': end_lat,
                'end_longitude': end_lng
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.uber_base_url}/v1.2/estimates/price"
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_uber_response(data, product_type)
                    else:
                        logger.warning(f"Uber API request failed with status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Uber API: {str(e)}")
            return None

    def _parse_uber_response(self, data: Dict, product_type: str) -> Optional[Dict]:
        """Parse Uber API response and format for frontend"""
        
        prices = data.get('prices', [])
        
        # Find the requested product type
        for price in prices:
            if price.get('display_name', '').lower().replace(' ', '') == product_type.lower():
                return self._format_price_data(price)
        
        # If specific product not found, return first available
        if prices:
            return self._format_price_data(prices[0])
        
        return None

    def _format_price_data(self, price: Dict) -> Dict:
        """Format price data for consistent frontend consumption"""
        
        low_estimate = price.get('low_estimate', 0)
        high_estimate = price.get('high_estimate', 0)
        average_estimate = (low_estimate + high_estimate) / 2 if low_estimate and high_estimate else 0
        
        return {
            'estimate': average_estimate,
            'low_estimate': low_estimate,
            'high_estimate': high_estimate,
            'formatted_estimate': f"${average_estimate:.2f}" if average_estimate else "N/A",
            'formatted_range': f"${low_estimate:.2f} - ${high_estimate:.2f}" if low_estimate and high_estimate else "N/A",
            'currency_code': price.get('currency_code', 'USD'),
            'display_name': price.get('display_name'),
            'duration': price.get('duration'),  # in seconds
            'distance': price.get('distance'),  # in meters
            'surge_multiplier': price.get('surge_multiplier', 1.0),
            'source': 'uber_api'
        }

# Global instance
uber_pricing_service = UberPricingService()