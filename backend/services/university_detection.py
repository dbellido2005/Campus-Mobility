import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from groq import Groq
from datetime import datetime, timedelta
import re

class UniversityDetectionService:
    """AI-powered university detection and nearby community mapping using Groq"""
    
    def __init__(self):
        self.groq_client = None
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = timedelta(days=7)  # Cache for 7 days
        
        # Standardized community names mapping
        self.community_name_mapping = {
            # Claremont Colleges variations
            'pomona': 'Pomona',
            'pomona college': 'Pomona',
            'pomona college california': 'Pomona',
            'harvey mudd': 'Harvey Mudd',
            'harvey mudd college': 'Harvey Mudd',
            'hmc': 'Harvey Mudd',
            'scripps': 'Scripps',
            'scripps college': 'Scripps',
            'pitzer': 'Pitzer',
            'pitzer college': 'Pitzer',
            'cmc': 'CMC',
            'claremont mckenna': 'CMC',
            'claremont mckenna college': 'CMC',
            'claremont colleges': '5C',
            '5c': '5C',
            'five colleges': '5C',
            'claremont consortium': '5C',
            
            # Common university name variations
            'usc': 'USC',
            'university of southern california': 'USC',
            'ucla': 'UCLA',
            'university of california los angeles': 'UCLA',
            'cal tech': 'Caltech',
            'california institute of technology': 'Caltech',
            'caltech': 'Caltech',
            
            # Generic cleanup
            'open to all': 'Open to all',
            'unknown': None,  # Filter out unknown
        }
        
    def _get_groq_client(self):
        """Lazy initialization of Groq client"""
        if self.groq_client is None:
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise Exception("GROQ_API_KEY environment variable not set")
            self.groq_client = Groq(api_key=api_key)
        return self.groq_client
    
    def normalize_community_name(self, name: str) -> Optional[str]:
        """
        Normalize community/university names to ensure consistency
        """
        if not name:
            return None
            
        # Convert to lowercase for matching
        normalized_key = name.lower().strip()
        
        # Check if we have a mapping for this name
        if normalized_key in self.community_name_mapping:
            return self.community_name_mapping[normalized_key]
        
        # If no exact match, try partial matches for common patterns
        # This handles cases where AI might add extra words
        for key, value in self.community_name_mapping.items():
            if key in normalized_key or normalized_key in key:
                return value
        
        # If no mapping found, return title case version of original
        return name.title()
        
    def detect_university_from_email(self, email: str) -> Dict[str, any]:
        """
        Detect university information from email domain using Groq AI
        
        Args:
            email: User's email address
            
        Returns:
            Dictionary with university information or error
        """
        try:
            # Extract domain
            domain = email.split('@')[1].lower() if '@' in email else ''
            
            # Basic validation
            if not domain.endswith('.edu'):
                return {
                    'valid': False,
                    'error': 'Only .edu email addresses are allowed'
                }
            
            # Check cache first
            if domain in self.cache:
                cache_entry = self.cache[domain]
                if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                    return cache_entry['data']
            
            # Use Groq to identify university
            university_info = self._query_groq_for_university(domain)
            
            if university_info['valid']:
                # Cache the result
                self.cache[domain] = {
                    'data': university_info,
                    'timestamp': datetime.now()
                }
                
                # Get nearby universities
                nearby_universities = self._get_nearby_universities(university_info)
                university_info['nearby_universities'] = nearby_universities
                
            return university_info
            
        except Exception as e:
            logging.error(f"Error in university detection: {e}")
            return {
                'valid': False,
                'error': 'Unable to detect university information'
            }
    
    def _query_groq_for_university(self, domain: str) -> Dict[str, any]:
        """
        Query Groq API to get university information from domain
        """
        try:
            prompt = f"""
            Analyze the email domain "{domain}" and provide detailed information about the university.
            
            Please respond with a JSON object containing:
            {{
                "valid": boolean (true if this is a valid university domain),
                "university_name": "Full official name of the university",
                "short_name": "Common abbreviation or short name",
                "city": "City where university is located",
                "state": "State/Province where university is located",
                "country": "Country where university is located",
                "university_type": "public" or "private",
                "student_population": approximate number of students (integer),
                "founded_year": year university was founded (integer),
                "notable_programs": ["list", "of", "notable", "academic", "programs"],
                "coordinates": {{
                    "latitude": decimal latitude,
                    "longitude": decimal longitude
                }}
            }}
            
            If the domain is not a valid university domain, return:
            {{
                "valid": false,
                "error": "Domain not recognized as a valid university"
            }}
            
            Only respond with valid JSON, no additional text.
            """
            
            response = self._get_groq_client().chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert on universities and educational institutions worldwide. Provide accurate, factual information about universities based on their email domains."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            university_data = json.loads(content)
            
            # Validate required fields
            if university_data.get('valid', False):
                required_fields = ['university_name', 'short_name', 'city', 'state', 'country']
                if all(field in university_data for field in required_fields):
                    return university_data
                else:
                    return {
                        'valid': False,
                        'error': 'Incomplete university information received'
                    }
            else:
                return {
                    'valid': False,
                    'error': university_data.get('error', 'Domain not recognized as a valid university')
                }
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {e}")
            return {
                'valid': False,
                'error': 'Invalid response format from AI service'
            }
        except Exception as e:
            logging.error(f"Groq API error: {e}")
            return {
                'valid': False,
                'error': 'University detection service temporarily unavailable'
            }
    
    def _get_nearby_universities(self, university_info: Dict[str, any]) -> List[Dict[str, any]]:
        """
        Get nearby universities for community selection using Groq AI
        """
        try:
            city = university_info.get('city', '')
            state = university_info.get('state', '')
            university_name = university_info.get('university_name', '')
            
            prompt = f"""
            Given that a user is from {university_name} in {city}, {state}, suggest 3-6 nearby universities that students might want to share rides with.
            
            IMPORTANT CONSTRAINTS:
            - ONLY include universities within 10 miles of {city}, {state}
            - Prioritize universities within 5 miles first
            - Focus on universities that are practical for ride-sharing (not long-distance travel)
            - Include community colleges and smaller institutions if they are nearby
            - If there are fewer than 3 universities within 10 miles, you may include up to 2 universities within 15 miles maximum
            
            Consider:
            - Universities in the same city or immediate neighboring cities
            - Institutions that students would realistically share rides to for daily commuting
            - Both 4-year universities and community colleges
            - Public and private institutions
            
            Respond with a JSON array of university objects, sorted by distance (closest first):
            [
                {{
                    "name": "Full university name",
                    "short_name": "Common abbreviation",
                    "city": "City name",
                    "distance_miles": approximate distance in miles (integer, must be 15 or less),
                    "relationship": "Description of why students might share rides (e.g., 'Same city', 'Neighboring city', 'Daily commute route')"
                }}
            ]
            
            Only respond with valid JSON array, no additional text.
            """
            
            response = self._get_groq_client().chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert on university geography and student travel patterns. Provide practical suggestions for nearby universities where students might share rides."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            nearby_universities = json.loads(content)
            
            # Validate the response is a list and filter by distance
            if isinstance(nearby_universities, list):
                # Filter out universities that are too far away (safety check)
                filtered_universities = []
                for uni in nearby_universities:
                    distance = uni.get('distance_miles', 0)
                    if isinstance(distance, (int, float)) and distance <= 15:
                        filtered_universities.append(uni)
                    else:
                        logging.warning(f"Filtered out university {uni.get('name', 'Unknown')} - distance {distance} miles is too far")
                
                return filtered_universities
            else:
                return []
                
        except Exception as e:
            logging.error(f"Error getting nearby universities: {e}")
            return []
    
    def validate_university_email(self, email: str) -> Dict[str, any]:
        """
        Enhanced email validation with AI-powered university detection
        
        This replaces the old validate_college_email function
        """
        return self.detect_university_from_email(email)
    
    def get_community_options_for_university(self, university_info: Dict[str, any]) -> List[str]:
        """
        Get community options for ride sharing based on university and nearby institutions
        """
        try:
            communities = []
            
            # Add the user's own university (normalized)
            short_name = university_info.get('short_name', '')
            if short_name:
                normalized_name = self.normalize_community_name(short_name)
                if normalized_name and normalized_name not in communities:
                    communities.append(normalized_name)
            
            # Add nearby universities (normalized)
            nearby_universities = university_info.get('nearby_universities', [])
            for nearby in nearby_universities:
                nearby_short_name = nearby.get('short_name', '')
                if nearby_short_name:
                    normalized_nearby = self.normalize_community_name(nearby_short_name)
                    if normalized_nearby and normalized_nearby not in communities:
                        communities.append(normalized_nearby)
            
            # Don't add "Open to all" automatically - it's filtered out in frontend now
            
            return communities
            
        except Exception as e:
            logging.error(f"Error getting community options: {e}")
            return []

# Global instance
university_service = UniversityDetectionService()