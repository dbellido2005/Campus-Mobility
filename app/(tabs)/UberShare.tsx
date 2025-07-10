import 'react-native-get-random-values';
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  Keyboard,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as Location from 'expo-location';
import ProperLocationInput from '@/components/ProperLocationInput';
import TimeRangeSlider from '@/components/TimeRangeSlider';
import { getCommunityOptions, getCommunityDisplayName, CommunityOptions } from '@/utils/universityUtils';

interface LocationData {
  description: string;
  latitude?: number;
  longitude?: number;
}

const API_BASE_URL = 'http://172.28.119.64:8000';

export default function ShareScreen() {
  const [whereFrom, setWhereFrom] = useState<LocationData>({ description: '' });
  const [whereTo, setWhereTo] = useState<LocationData>({ description: '' });
  const [departureDate, setDepartureDate] = useState(new Date());
  const [earliestTime, setEarliestTime] = useState(480); // 8:00 AM in minutes
  const [latestTime, setLatestTime] = useState(600); // 10:00 AM in minutes
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedCommunities, setSelectedCommunities] = useState<string[]>([]);
  const [posting, setPosting] = useState(false);
  const [priceEstimate, setPriceEstimate] = useState<any>(null);
  const [loadingEstimate, setLoadingEstimate] = useState(false);
  const [routeInfo, setRouteInfo] = useState<any>(null);
  const [loadingRouteInfo, setLoadingRouteInfo] = useState(false);
  const [communityOptions, setCommunityOptions] = useState<CommunityOptions | null>(null);
  const [loadingCommunities, setLoadingCommunities] = useState(true);

  // Load community options on component mount
  useEffect(() => {
    loadCommunityOptions();
  }, []);

  // Auto-calculate price estimate and route info when both locations are set
  useEffect(() => {
    if (whereFrom.latitude && whereFrom.longitude && whereTo.latitude && whereTo.longitude) {
      getPriceEstimate();
      getRouteInfo();
    } else {
      setPriceEstimate(null);
      setRouteInfo(null);
    }
  }, [whereFrom, whereTo]);

  const loadCommunityOptions = async () => {
    try {
      setLoadingCommunities(true);
      const options = await getCommunityOptions();
      setCommunityOptions(options);
      
      // Auto-select user's own university community
      if (options.user_university.short_name) {
        setSelectedCommunities([options.user_university.short_name]);
      }
    } catch (error) {
      console.error('Failed to load community options:', error);
      Alert.alert('Error', 'Failed to load community options');
    } finally {
      setLoadingCommunities(false);
    }
  };

  const refreshUniversityInfo = async () => {
    try {
      setLoadingCommunities(true);
      const token = await AsyncStorage.getItem('userToken');
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/refresh-university-info`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        Alert.alert('Success', 'University information updated! Communities will refresh automatically.');
        // Reload communities after refresh
        await loadCommunityOptions();
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to refresh university information');
      }
    } catch (error) {
      console.error('Error refreshing university info:', error);
      Alert.alert('Error', 'Unable to refresh university information');
    } finally {
      setLoadingCommunities(false);
    }
  };

  const setCurrentLocationAsSelected = async (isFrom: boolean) => {
    try {
      // Always get fresh location
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied', 'Location permission is required for this feature.');
        return;
      }

      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });

      // Get actual address from coordinates
      const address = await Location.reverseGeocodeAsync({
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      });

      let description = 'Current Location';
      if (address.length > 0) {
        const addr = address[0];
        // Format address nicely
        const parts = [];
        if (addr.name) parts.push(addr.name);
        if (addr.street) parts.push(addr.street);
        if (addr.city) parts.push(addr.city);
        if (addr.region) parts.push(addr.region);
        
        description = parts.length > 0 ? parts.join(', ') : 
          `${location.coords.latitude.toFixed(4)}, ${location.coords.longitude.toFixed(4)}`;
      }

      const locationData: LocationData = {
        description,
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      };

      if (isFrom) {
        setWhereFrom(locationData);
      } else {
        setWhereTo(locationData);
      }
    } catch (error) {
      console.error('Error getting current location:', error);
      Alert.alert('Location Error', 'Unable to get your current location. Please check your location settings.');
    }
  };

  const toggleCommunity = (community: string) => {
    setSelectedCommunities((prev) =>
      prev.includes(community)
        ? prev.filter((c) => c !== community)
        : [...prev, community]
    );
  };

  const handleTimeRangeChange = (earliest: number, latest: number) => {
    setEarliestTime(earliest);
    setLatestTime(latest);
  };

  const getPriceEstimate = async () => {
    if (!whereFrom.latitude || !whereFrom.longitude || !whereTo.latitude || !whereTo.longitude) {
      return;
    }

    try {
      setLoadingEstimate(true);
      const token = await AsyncStorage.getItem('userToken');
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/price-estimate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          origin: whereFrom,
          destination: whereTo,
          product_type: 'uberX'
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.pricing) {
          setPriceEstimate(data.pricing);
        } else {
          // Uber API unavailable
          setPriceEstimate({ unavailable: true, message: data.message || "Price estimate unavailable" });
        }
      } else {
        console.error('Failed to get price estimate');
        setPriceEstimate({ unavailable: true, message: "Price estimate unavailable" });
      }
    } catch (error) {
      console.error('Error getting price estimate:', error);
      setPriceEstimate(null);
    } finally {
      setLoadingEstimate(false);
    }
  };

  const getRouteInfo = async () => {
    if (!whereFrom.latitude || !whereFrom.longitude || !whereTo.latitude || !whereTo.longitude) {
      return;
    }

    try {
      setLoadingRouteInfo(true);
      const token = await AsyncStorage.getItem('userToken');
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/route-info`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          origin: whereFrom,
          destination: whereTo
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Route info received:', data);
        setRouteInfo(data.route_info);
      } else {
        console.error('Failed to get route info');
        setRouteInfo({ unavailable: true, message: "Route info unavailable" });
      }
    } catch (error) {
      console.error('Error getting route info:', error);
      setRouteInfo(null);
    } finally {
      setLoadingRouteInfo(false);
    }
  };

  const postRideRequest = async () => {
    try {
      setPosting(true);

      // Validation
      if (!whereFrom.description || !whereTo.description) {
        Alert.alert('Error', 'Please select both origin and destination');
        return;
      }

      if (selectedCommunities.length === 0) {
        Alert.alert('Error', 'Please select at least one community');
        return;
      }

      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const rideData = {
        origin: whereFrom,
        destination: whereTo,
        departure_date: departureDate.toISOString(),
        earliest_time: earliestTime,
        latest_time: latestTime,
        communities: selectedCommunities,
        max_participants: 4
      };

      console.log('Sending ride data:', JSON.stringify(rideData, null, 2));

      const response = await fetch(`${API_BASE_URL}/ride-request`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(rideData)
      });

      if (response.ok) {
        Alert.alert(
          'Success',
          'Your ride request has been posted!',
          [
            {
              text: 'OK',
              onPress: () => {
                // Reset form
                setWhereFrom({ description: '' });
                setWhereTo({ description: '' });
                setDepartureDate(new Date());
                setEarliestTime(480);
                setLatestTime(600);
                setSelectedCommunities([]);
              }
            }
          ]
        );
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to post ride request');
      }
    } catch (error) {
      console.error('Error posting ride request:', error);
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setPosting(false);
    }
  };

  return (
    <ScrollView 
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
      onScrollBeginDrag={() => Keyboard.dismiss()}
    >
      <Text style={styles.title}>Uber Share</Text>
      
      {/* Where From */}
      <ProperLocationInput
        placeholder="Where from?"
        value={whereFrom}
        onLocationSelect={setWhereFrom}
        onCurrentLocation={() => setCurrentLocationAsSelected(true)}
      />

      {/* Where To */}
      <ProperLocationInput
        placeholder="Where to?"
        value={whereTo}
        onLocationSelect={setWhereTo}
        onCurrentLocation={() => setCurrentLocationAsSelected(false)}
      />

      {/* Price Estimate */}
      {(priceEstimate || loadingEstimate) && (
        <View style={styles.priceEstimateSection}>
          <Text style={styles.sectionLabel}>Price Estimate</Text>
          {loadingEstimate ? (
            <View style={styles.estimateContainer}>
              <Text style={styles.estimateLoading}>Calculating...</Text>
            </View>
          ) : priceEstimate ? (
            <View style={styles.estimateContainer}>
              {priceEstimate.unavailable ? (
                <View style={styles.unavailableContainer}>
                  <Text style={styles.unavailableText}>Price estimate unavailable</Text>
                  <Text style={styles.unavailableSubtext}>
                    {priceEstimate.message || "Uber API is not accessible"}
                  </Text>
                </View>
              ) : (
                <>
                  <View style={styles.estimateHeader}>
                    <Text style={styles.estimatePrice}>{priceEstimate.formatted_estimate}</Text>
                    {priceEstimate.formatted_range && (
                      <Text style={styles.estimateRange}>({priceEstimate.formatted_range})</Text>
                    )}
                  </View>
                  <View style={styles.estimateDetails}>
                    {priceEstimate.distance && (
                      <Text style={styles.estimateDetail}>
                        Distance: {(priceEstimate.distance / 1000).toFixed(1)} km
                      </Text>
                    )}
                    {priceEstimate.duration && (
                      <Text style={styles.estimateDetail}>
                        Duration: {Math.round(priceEstimate.duration / 60)} min
                      </Text>
                    )}
                    {priceEstimate.surge_multiplier > 1 && (
                      <Text style={styles.surgeText}>
                        Surge pricing active ({priceEstimate.surge_multiplier}x)
                      </Text>
                    )}
                  </View>
                  <Text style={styles.estimateSource}>via Uber API</Text>
                </>
              )}
            </View>
          ) : null}
        </View>
      )}

      {(routeInfo || loadingRouteInfo) && (
        <View style={styles.routeInfoSection}>
          <Text style={styles.sectionLabel}>Route Information</Text>
          {loadingRouteInfo ? (
            <View style={styles.estimateContainer}>
              <Text style={styles.estimateLoading}>Calculating route...</Text>
            </View>
          ) : routeInfo ? (
            <View style={styles.estimateContainer}>
              {routeInfo.unavailable ? (
                <View style={styles.unavailableContainer}>
                  <Text style={styles.unavailableText}>Route info unavailable</Text>
                  <Text style={styles.unavailableSubtext}>
                    {routeInfo.message || "Google Routes API is not accessible"}
                  </Text>
                </View>
              ) : (
                <>
                  <View style={styles.routeHeader}>
                    <View style={styles.routeStatsContainer}>
                      <Text style={styles.routeStatsTitle}>
                        {routeInfo.formatted_distance} • {routeInfo.formatted_duration}
                      </Text>
                    </View>
                  </View>
                  <View style={styles.estimateDetails}>
                    <Text style={styles.estimateDetail}>
                      Distance: {routeInfo.formatted_distance}
                    </Text>
                    <Text style={styles.estimateDetail}>
                      Travel time: {routeInfo.formatted_duration}
                    </Text>
                  </View>
                  <Text style={styles.estimateSource}>via Google Routes API</Text>
                </>
              )}
            </View>
          ) : null}
        </View>
      )}

      {/* Departure Date */}
      <View style={styles.dateSection}>
        <Text style={styles.sectionLabel}>Departure Date</Text>
        <TouchableOpacity
          style={styles.input}
          onPress={() => setShowDatePicker(true)}
        >
          <Text style={styles.placeholderText}>
            {departureDate.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </Text>
        </TouchableOpacity>
        {showDatePicker && (
          <DateTimePicker
            value={departureDate}
            mode="date"
            display="default"
            minimumDate={new Date()}
            onChange={(_, date) => {
              if (date) setDepartureDate(date);
              setShowDatePicker(false);
            }}
          />
        )}
      </View>

      {/* Time Range Slider */}
      <TimeRangeSlider
        earliestTime={earliestTime}
        latestTime={latestTime}
        onTimeChange={handleTimeRangeChange}
      />


      {/* Community */}
      <View style={styles.communitySection}>
        <View style={styles.communitySectionHeader}>
          <Text style={styles.sectionLabel}>Community</Text>
          <TouchableOpacity
            style={styles.refreshButton}
            onPress={refreshUniversityInfo}
            disabled={loadingCommunities}
          >
            <Text style={styles.refreshButtonText}>
              {loadingCommunities ? 'Refreshing...' : 'Refresh'}
            </Text>
          </TouchableOpacity>
        </View>
        <View style={styles.communityContainer}>
          {loadingCommunities ? (
            <Text style={styles.loadingText}>Loading communities...</Text>
          ) : (
            <>
              {communityOptions?.communities.map((community) => (
              <TouchableOpacity
                key={community}
                style={[
                  styles.communityOption,
                  selectedCommunities.includes(community) && styles.communitySelected,
                ]}
                onPress={() => toggleCommunity(community)}
              >
                <Text
                  style={{
                    color: selectedCommunities.includes(community) ? 'white' : '#333',
                  }}
                >
                  {getCommunityDisplayName(community)}
                </Text>
              </TouchableOpacity>
            ))}
            
              {/* Show university info for context */}
              {communityOptions && communityOptions.source === 'ai_powered' && (
                <View style={styles.universityInfoContainer}>
                  <Text style={styles.universityInfoText}>
                    📍 {communityOptions.user_university.name}
                  </Text>
                  <Text style={styles.universityInfoSubtext}>
                    {communityOptions.user_university.city}, {communityOptions.user_university.state}
                  </Text>
                  {communityOptions.nearby_universities.length > 0 && (
                    <Text style={styles.nearbyText}>
                      + {communityOptions.nearby_universities.length} nearby universities
                    </Text>
                  )}
                </View>
              )}
            </>
          )}
        </View>
      </View>

      <TouchableOpacity 
        style={[styles.doneButton, posting && styles.doneButtonDisabled]} 
        onPress={postRideRequest}
        disabled={posting}
      >
        <Text style={{ color: 'white', fontWeight: 'bold' }}>
          {posting ? 'Posting...' : 'Post Ride Request'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    gap: 16,
    paddingBottom: 100, // Extra padding for better scrolling
  },
  dateSection: {
    marginBottom: 8,
  },
  sectionLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#fff',
    justifyContent: 'center',
  },
  placeholderText: {
    color: '#666',
  },
  communitySection: {
    marginBottom: 20,
  },
  communitySectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  refreshButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '500',
  },
  communityContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  communityOption: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#eee',
    borderRadius: 20,
  },
  communitySelected: {
    backgroundColor: '#2b6cb0',
  },
  loadingText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    paddingVertical: 20,
  },
  universityInfoContainer: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#f0f8ff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e7ff',
    width: '100%',
  },
  universityInfoText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  universityInfoSubtext: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  nearbyText: {
    fontSize: 11,
    color: '#4338ca',
    fontStyle: 'italic',
  },
  doneButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 30,
    marginTop: 32,
  },
  doneButtonDisabled: {
    backgroundColor: '#cccccc',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    marginTop: 70,
  },
  priceEstimateSection: {
    marginTop: 20,
    marginBottom: 20,
  },
  routeInfoSection: {
    marginTop: 20,
    marginBottom: 20,
  },
  estimateContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  estimateHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  estimatePrice: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2196F3',
    marginRight: 8,
  },
  estimateRange: {
    fontSize: 14,
    color: '#666',
  },
  estimateDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 8,
  },
  estimateDetail: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#fff',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  surgeText: {
    fontSize: 12,
    color: '#FF5722',
    backgroundColor: '#FFF3E0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    fontWeight: '500',
  },
  estimateSource: {
    fontSize: 10,
    color: '#999',
    textAlign: 'center',
    marginTop: 4,
  },
  routeHeader: {
    alignItems: 'center',
    marginBottom: 12,
  },
  routeStatsContainer: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
  },
  routeStatsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1976d2',
    textAlign: 'center',
  },
  estimateLoading: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  unavailableContainer: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  unavailableText: {
    fontSize: 16,
    color: '#FF5722',
    fontWeight: '500',
    marginBottom: 4,
  },
  unavailableSubtext: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
});