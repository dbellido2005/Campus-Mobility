from fastapi import APIRouter, HTTPException, status, Depends
from utils.auth_utils import get_current_user
from services.university_detection import university_service
from database import users_collection
from typing import List, Dict, Any

router = APIRouter()

@router.get("/community-options")
async def get_community_options(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get dynamic community options for ride sharing based on user's university
    """
    try:
        # Get user's university information
        user_email = current_user.get('email')
        user_doc = await users_collection.find_one({"email": user_email})
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user has university_info (from AI detection)
        university_info = user_doc.get('university_info')
        
        if university_info:
            # Use AI-powered community detection
            communities = university_service.get_community_options_for_university(university_info)
            
            # Get detailed information about nearby universities
            nearby_universities = university_info.get('nearby_universities', [])
            
            return {
                "communities": communities,
                "user_university": {
                    "name": university_info.get('university_name'),
                    "short_name": university_info.get('short_name'),
                    "city": university_info.get('city'),
                    "state": university_info.get('state')
                },
                "nearby_universities": nearby_universities,
                "source": "ai_powered"
            }
        else:
            # Fallback to legacy hardcoded communities for known institutions
            college = user_doc.get('college', '')
            
            legacy_communities = _get_legacy_communities(college)
            
            return {
                "communities": legacy_communities,
                "user_university": {
                    "name": college,
                    "short_name": college.split(' ')[0] if college else '',
                    "city": "Unknown",
                    "state": "Unknown"
                },
                "nearby_universities": [],
                "source": "legacy"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get community options"
        )

def _get_legacy_communities(college: str) -> List[str]:
    """Legacy hardcoded community mapping for known institutions"""
    
    # Claremont Colleges mapping
    claremont_communities = ['Pomona', 'Harvey Mudd', 'Scripps', 'Pitzer', 'CMC', '5C']
    
    legacy_mapping = {
        'Pomona College': claremont_communities,
        'Harvey Mudd College': claremont_communities,
        'Scripps College': claremont_communities,
        'Pitzer College': claremont_communities,
        'Claremont McKenna College': claremont_communities,
        'Carnegie Mellon University': ['CMU', 'University of Pittsburgh', 'Duquesne University', 'Pittsburgh area']
    }
    
    return legacy_mapping.get(college, ['Open to all'])

@router.get("/nearby-universities/{university_name}")
async def get_nearby_universities(university_name: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get nearby universities for a specific university using AI detection
    """
    try:
        # Create a mock university info object to get nearby universities
        university_info = {
            'university_name': university_name,
            'city': 'Unknown',
            'state': 'Unknown'
        }
        
        nearby_universities = university_service._get_nearby_universities(university_info)
        
        return {
            "university": university_name,
            "nearby_universities": nearby_universities,
            "source": "ai_powered"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get nearby universities"
        )

@router.post("/refresh-university-info")
async def refresh_university_info(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Refresh user's university information using AI detection
    """
    try:
        user_email = current_user.get('email')
        
        # Clear cache to force fresh detection
        if hasattr(university_service, 'cache'):
            university_service.cache = {}
        
        # Re-detect university information
        university_detection = university_service.detect_university_from_email(user_email)
        
        if university_detection['valid']:
            # Update user's university_info in database
            from models import UniversityInfo
            university_info = UniversityInfo(**university_detection)
            
            await users_collection.update_one(
                {"email": user_email},
                {"$set": {"university_info": university_info.dict()}}
            )
            
            return {
                "message": "University information refreshed successfully",
                "university_info": university_detection
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=university_detection.get('error', 'Failed to detect university')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh university information"
        )