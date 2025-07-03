# Uber Sandbox API Integration Setup Guide

## Implementation Overview

This is a **simple Uber Sandbox API integration** that:
- ✅ Uses **only** Uber Sandbox API for price estimates
- ✅ Shows **"Price estimate unavailable"** when Uber API is not accessible
- ✅ **No fallback pricing calculations** or custom algorithms
- ✅ **Sandbox mode** for safe testing

## Important Notice (2025)

**⚠️ Uber Rides API Deprecation**: As of 2025, Uber has deprecated their public Rides API for new applications. This implementation provides a clean integration for those who have existing API access.

## Setup Instructions

### 1. Uber API Setup
If you have existing Uber API access:

1. Visit [Uber Developer Dashboard](https://developer.uber.com/)
2. Sign in or create an account
3. Create a new app
4. Get your credentials:
   - Client ID
   - Client Secret
   - Server Token (if available)
5. Add to your `.env` file:
   ```
   UBER_CLIENT_ID=your-uber-client-id
   UBER_CLIENT_SECRET=your-uber-client-secret
   UBER_SERVER_TOKEN=your-uber-server-token
   UBER_SANDBOX_MODE=true
   ```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Uber API Configuration
UBER_SERVER_TOKEN=your-uber-server-token
UBER_SANDBOX_MODE=true
```

**Note**: Only the server token is required for price estimates.

## API Endpoints

### Price Estimation
```http
POST /price-estimate
Authorization: Bearer <token>
Content-Type: application/json

{
  "origin": {
    "latitude": 34.0522,
    "longitude": -118.2437,
    "description": "Los Angeles, CA"
  },
  "destination": {
    "latitude": 34.1478,
    "longitude": -118.1445,
    "description": "Pasadena, CA"
  },
  "product_type": "uberX"
}
```

### Response Format
```json
{
  "success": true,
  "pricing": {
    "estimate": 25.50,
    "low_estimate": 22.95,
    "high_estimate": 28.05,
    "formatted_estimate": "$25.50",
    "formatted_range": "$22.95 - $28.05",
    "currency_code": "USD",
    "duration": 1800,
    "distance": 15.2,
    "surge_multiplier": 1.2,
    "confidence": 0.8,
    "source": "enhanced_calculation",
    "breakdown": {
      "base_fare": 2.50,
      "distance_cost": 18.36,
      "time_cost": 9.00,
      "surge_applied": true
    }
  }
}
```

## Pricing Algorithm Details

### Base Pricing Structure
- **Base Fare**: $2.50
- **Cost per KM**: $1.80
- **Cost per Minute**: $0.30
- **Minimum Fare**: $5.00

### Surge Multipliers
- **Rush Hours** (7-9 AM, 5-7 PM): 1.3x
- **Late Night** (10 PM - 5 AM): 1.2x
- **Lunch Time** (12-1 PM): 1.1x
- **Regular Hours**: 1.0x

### Distance Calculation
1. **Google Maps API**: Most accurate (if configured)
2. **Haversine Formula**: Fallback great-circle distance
3. **Speed Estimates**:
   - < 5km: 25 km/h (city driving)
   - 5-20km: 40 km/h (mixed driving)
   - > 20km: 60 km/h (highway driving)

## Testing

### Sandbox Testing
The system automatically uses sandbox mode when `UBER_SANDBOX_MODE=true`. This allows testing without real charges.

### Test Endpoints
```bash
# Test price estimation
curl -X POST http://localhost:8000/price-estimate \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"latitude": 34.0522, "longitude": -118.2437},
    "destination": {"latitude": 34.1478, "longitude": -118.1445}
  }'
```

## Error Handling

The system gracefully handles:
- ❌ Uber API unavailable
- ❌ Google Maps API rate limits
- ❌ Network timeouts
- ❌ Invalid coordinates
- ✅ Always provides fallback pricing

## Future Enhancements

### Possible Integrations
1. **Local Transit APIs** for public transport options
2. **Weather APIs** for weather-based surge pricing
3. **Event APIs** for event-based demand prediction
4. **Real-time Traffic** for more accurate duration estimates

### Uber Alternatives
Consider integrating with:
- **Lyft API** (if available)
- **Local taxi companies**
- **Ride-sharing platforms** specific to your region

## Troubleshooting

### Common Issues

1. **"No price estimate available"**
   - Check Google Maps API key
   - Verify coordinates are valid
   - Ensure network connectivity

2. **"Uber API not responding"**
   - Normal behavior - fallback system will work
   - Check sandbox mode setting
   - Verify API credentials (if using Uber)

3. **Inaccurate pricing**
   - Configure Google Maps API for better accuracy
   - Adjust pricing parameters in `pricing_service.py`
   - Check surge multiplier logic

### Logs and Monitoring
Enable detailed logging in `pricing_service.py` to monitor:
- API call success/failure rates
- Fallback usage patterns
- Pricing accuracy
- Performance metrics

## Cost Considerations

### Google Maps API Pricing
- **Distance Matrix API**: $5 per 1,000 requests
- **First 200 requests/month**: Free
- **Estimated cost** for 10,000 rides/month: ~$40

### Optimization Tips
- Cache results for frequent routes
- Batch requests when possible
- Use coordinate-based caching
- Implement request rate limiting

---

**Note**: This implementation provides a production-ready pricing system that works independently of Uber's API availability, ensuring your application remains functional regardless of external API changes.