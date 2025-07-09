import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://172.28.119.64:8000';

export interface UniversityInfo {
  university_name: string;
  short_name: string;
  city?: string;
  state?: string;
  country?: string;
  university_type?: string;
  student_population?: number;
  founded_year?: number;
  notable_programs?: string[];
  coordinates?: { latitude: number; longitude: number };
  nearby_universities?: NearbyUniversity[];
  legacy?: boolean;
  fallback?: boolean;
}

export interface NearbyUniversity {
  name: string;
  short_name: string;
  city: string;
  distance_miles: number;
  relationship: string;
}

export interface CommunityOptions {
  communities: string[];
  user_university: {
    name: string;
    short_name: string;
    city: string;
    state: string;
  };
  nearby_universities: NearbyUniversity[];
  source: 'ai_powered' | 'legacy';
}

/**
 * Get dynamic community options for the current user
 */
export const getCommunityOptions = async (): Promise<CommunityOptions> => {
  try {
    const token = await AsyncStorage.getItem('userToken');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/community-options`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching community options:', error);
    
    // Fallback to legacy Claremont Colleges communities
    return {
      communities: ['Pomona', 'Harvey Mudd', 'Scripps', 'Pitzer', 'CMC', '5C'],
      user_university: {
        name: 'Unknown University',
        short_name: 'Unknown',
        city: 'Unknown',
        state: 'Unknown'
      },
      nearby_universities: [],
      source: 'legacy'
    };
  }
};

/**
 * Get nearby universities for a specific university
 */
export const getNearbyUniversities = async (universityName: string): Promise<NearbyUniversity[]> => {
  try {
    const token = await AsyncStorage.getItem('userToken');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/nearby-universities/${encodeURIComponent(universityName)}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.nearby_universities || [];
  } catch (error) {
    console.error('Error fetching nearby universities:', error);
    return [];
  }
};

/**
 * Refresh user's university information using AI detection
 */
export const refreshUniversityInfo = async (): Promise<UniversityInfo> => {
  try {
    const token = await AsyncStorage.getItem('userToken');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/refresh-university-info`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.university_info;
  } catch (error) {
    console.error('Error refreshing university info:', error);
    throw error;
  }
};

/**
 * Format university name for display
 */
export const formatUniversityName = (universityInfo: UniversityInfo): string => {
  if (universityInfo.legacy) {
    return universityInfo.university_name;
  }
  
  const { university_name, city, state } = universityInfo;
  if (city && state) {
    return `${university_name} (${city}, ${state})`;
  }
  return university_name;
};

/**
 * Get display name for community chip
 */
export const getCommunityDisplayName = (community: string): string => {
  // Handle legacy community names
  const displayMap: { [key: string]: string } = {
    'Harvey Mudd': 'HMC',
    'Claremont McKenna College': 'CMC',
    'Carnegie Mellon University': 'CMU',
    'University of Pittsburgh': 'Pitt',
    'Duquesne University': 'Duquesne',
    'Massachusetts Institute of Technology': 'MIT',
    'Harvard University': 'Harvard',
    'Northeastern University': 'Northeastern',
    'Tufts University': 'Tufts'
  };
  
  return displayMap[community] || community;
};

/**
 * Check if communities are from AI detection or legacy mapping
 */
export const isAIPowered = (source: string): boolean => {
  return source === 'ai_powered';
};