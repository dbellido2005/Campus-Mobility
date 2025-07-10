import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  Alert, 
  RefreshControl,
  Dimensions,
  Modal,
  Keyboard
} from 'react-native';
import { Card, Button, Chip, IconButton } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import MessagingScreen from '@/components/messaging/MessagingScreen';

const API_BASE_URL = 'http://172.28.119.64:8000';
const { width } = Dimensions.get('window');

interface LocationData {
  description: string;
  latitude?: number;
  longitude?: number;
}

interface RouteInfo {
  distance_meters: number;
  distance_miles: number;
  formatted_distance: string;
  duration_seconds: number;
  duration_minutes: number;
  formatted_duration: string;
  polyline: string;
  source: string;
}

interface RidePost {
  _id: string;
  origin: LocationData;
  destination: LocationData;
  departure_date: string;
  earliest_time: number;
  latest_time: number;
  communities: string[];
  creator_email: string;
  creator_name?: string;
  max_participants: number;
  available_spots: number;
  estimated_price_per_person?: number;
  estimated_travel_time?: number;
  status: string;
  user_ids: string[];
  route_info?: RouteInfo;
}

export default function ExploreScreen() {
  const [rides, setRides] = useState<RidePost[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentUserEmail, setCurrentUserEmail] = useState<string | null>(null);
  const [showMessaging, setShowMessaging] = useState(false);
  const [selectedRideId, setSelectedRideId] = useState<string | null>(null);

  useEffect(() => {
    fetchRides();
    getCurrentUserEmail();
  }, []);

  const getCurrentUserEmail = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      
      if (userData) {
        const user = JSON.parse(userData);
        setCurrentUserEmail(user.email);
      } else {
      }
    } catch (error) {
      console.error('Error getting user email:', error);
    }
  };

  const fetchRides = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride-requests`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Received rides:', JSON.stringify(data, null, 2));
        
        
        setRides(data);
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to load rides');
      }
    } catch (error) {
      console.error('Error fetching rides:', error);
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchRides();
  };

  const joinRide = async (rideId: string) => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride-request/${rideId}/join`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        Alert.alert('Success', result.message);
        fetchRides(); // Refresh the list
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to join ride');
      }
    } catch (error) {
      console.error('Error joining ride:', error);
      Alert.alert('Error', 'Unable to connect to server');
    }
  };

  const leaveRide = async (rideId: string) => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride-request/${rideId}/leave`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        Alert.alert('Success', result.message);
        fetchRides(); // Refresh the list
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to leave ride');
      }
    } catch (error) {
      console.error('Error leaving ride:', error);
      Alert.alert('Error', 'Unable to connect to server');
    }
  };

  const handleMessageRide = (rideId: string) => {
    setSelectedRideId(rideId);
    setShowMessaging(true);
  };

  const closeMessaging = () => {
    setShowMessaging(false);
    setSelectedRideId(null);
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours > 12 ? hours - 12 : hours === 0 ? 12 : hours;
    return `${displayHours}:${mins.toString().padStart(2, '0')} ${period}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTravelTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours === 0) {
      return `${mins} min`;
    } else if (mins === 0) {
      return `${hours} hr`;
    } else {
      return `${hours} hr ${mins} min`;
    }
  };

  const isUserJoined = (ride: RidePost) => {
    return currentUserEmail && 
           (ride.user_ids.includes(currentUserEmail) || ride.creator_email === currentUserEmail);
  };

  const isUserCreator = (ride: RidePost) => {
    return currentUserEmail && ride.creator_email === currentUserEmail;
  };

  const deleteRide = async (rideId: string) => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }


      const response = await fetch(`${API_BASE_URL}/ride-request/${rideId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });


      if (response.ok) {
        Alert.alert('Success', 'Ride deleted successfully');
        fetchRides(); // Refresh the ride list
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to delete ride');
      }
    } catch (error) {
      console.error('Error deleting ride:', error);
      Alert.alert('Error', 'Unable to delete ride');
    }
  };

  const handleDeleteRide = (rideId: string) => {
    Alert.alert(
      'Delete Ride',
      'Are you sure you want to delete this ride? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive', 
          onPress: () => deleteRide(rideId) 
        }
      ]
    );
  };

  const renderRouteDisplay = (ride: RidePost) => {
    
    return (
      <View style={styles.routeContainer}>
        <View style={styles.routeHeader}>
          <Text style={styles.routeTitle}>Route</Text>
          {ride.route_info && (
            <View style={styles.routeStatsContainer}>
              <Text style={styles.routeStats}>
                {ride.route_info.formatted_distance} • {ride.route_info.formatted_duration}
              </Text>
            </View>
          )}
        </View>
        <View style={styles.locationRow}>
          <View style={[styles.locationDot, { backgroundColor: '#4CAF50' }]} />
          <Text style={styles.locationText} numberOfLines={2}>
            {ride.origin.description}
          </Text>
        </View>
        <View style={styles.routeLine} />
        <View style={styles.locationRow}>
          <View style={[styles.locationDot, { backgroundColor: '#F44336' }]} />
          <Text style={styles.locationText} numberOfLines={2}>
            {ride.destination.description}
          </Text>
        </View>
      </View>
    );
  };

  const renderRideCard = (ride: RidePost) => (
    <Card key={ride._id} style={styles.rideCard}>
      <Card.Content>
        <View style={styles.rideLayout}>
          {/* Left side - Route Display */}
          <View style={styles.routeDisplayContainer}>
            {renderRouteDisplay(ride)}
          </View>

          {/* Right side - Details */}
          <View style={styles.detailsContainer}>
            <View style={styles.dateTimeContainer}>
              <Text style={styles.dateText}>{formatDate(ride.departure_date)}</Text>
              <Text style={styles.timeText}>
                {formatTime(ride.earliest_time)} - {formatTime(ride.latest_time)}
              </Text>
            </View>

            <View style={styles.communitiesContainer}>
              <Text style={styles.sectionLabel}>Communities:</Text>
              <View style={styles.chipContainer}>
                {ride.communities.map((community, index) => (
                  <Chip key={index} style={styles.communityChip} textStyle={styles.chipText}>
                    {community === 'Harvey Mudd' ? 'HMC' : 
                     community === 'Claremont McKenna College' ? 'CMC' : 
                     community}
                  </Chip>
                ))}
              </View>
            </View>

            <View style={styles.estimatesContainer}>
              {ride.estimated_travel_time && (
                <View style={styles.estimateItem}>
                  <Text style={styles.estimateLabel}>Travel Time:</Text>
                  <Text style={styles.estimateValue}>{formatTravelTime(ride.estimated_travel_time)}</Text>
                </View>
              )}
              {ride.estimated_total_price && (
                <View style={styles.estimateItem}>
                  <Text style={styles.estimateLabel}>Estimated total price:</Text>
                  <Text style={styles.estimateValue}>${ride.estimated_total_price.toFixed(2)}</Text>
                </View>
              )}
              <View style={styles.estimateItem}>
                <Text style={styles.estimateLabel}>Available spots:</Text>
                <Text style={styles.estimateValue}>{ride.available_spots}/{ride.max_participants}</Text>
              </View>
              {(ride.estimated_travel_time || ride.estimated_total_price) && (
                <Text style={styles.estimateDisclaimer}>
                  * Estimates provided by Uber API
                </Text>
              )}
            </View>

            {ride.creator_name && (
              <Text style={styles.creatorText}>
                Posted by: {ride.creator_name}
              </Text>
            )}
          </View>
        </View>

        {/* Full-width button container at the bottom */}
        <View style={styles.buttonContainer}>
          <Button
            mode="contained"
            onPress={() => isUserJoined(ride) ? leaveRide(ride._id) : joinRide(ride._id)}
            style={[
              styles.actionButton,
              isUserJoined(ride) && styles.leaveButton
            ]}
            disabled={ride.available_spots === 0 && !isUserJoined(ride)}
            buttonColor={isUserJoined(ride) ? '#FF5722' : '#4CAF50'}
            textColor="#FFFFFF"
            contentStyle={styles.buttonContent}
          >
            {ride.available_spots === 0 && !isUserJoined(ride) ? 'Full' : 
             isUserJoined(ride) ? 'Leave' : 'Join'}
          </Button>
          
          <Button
            mode="outlined"
            onPress={() => handleMessageRide(ride._id)}
            style={styles.messageButton}
            icon="message-text"
            textColor="#2196F3"
            contentStyle={styles.buttonContent}
          >
            Message
          </Button>
          
          {isUserCreator(ride) && (
            <Button
              mode="outlined"
              onPress={() => handleDeleteRide(ride._id)}
              style={styles.deleteButton}
              icon="delete"
              buttonColor="#ffebee"
              textColor="#d32f2f"
              contentStyle={styles.buttonContent}
            >
              Delete
            </Button>
          )}
        </View>
      </Card.Content>
    </Card>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading rides...</Text>
      </View>
    );
  }

  return (
    <>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        keyboardShouldPersistTaps="handled"
        onScrollBeginDrag={() => Keyboard.dismiss()}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Available Rides</Text>
          <IconButton
            icon="refresh"
            size={24}
            onPress={onRefresh}
          />
        </View>

        {rides.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No rides available for your community</Text>
            <Text style={styles.emptySubtext}>
              Check back later or create a ride in the Uber Share tab!
            </Text>
          </View>
        ) : (
          rides.map(renderRideCard)
        )}
      </ScrollView>

      <Modal
        visible={showMessaging}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        {selectedRideId && (
          <MessagingScreen
            rideId={selectedRideId}
            onBack={closeMessaging}
          />
        )}
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    paddingBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  rideCard: {
    margin: 16,
    marginBottom: 12,
    elevation: 4,
  },
  rideLayout: {
    flexDirection: 'row',
    gap: 16,
  },
  routeDisplayContainer: {
    width: width * 0.32,
    minHeight: 120,
  },
  routeContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    minHeight: 120,
    justifyContent: 'space-between',
  },
  routeHeader: {
    alignItems: 'center',
    marginBottom: 8,
  },
  routeTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
  },
  routeStatsContainer: {
    marginTop: 2,
    paddingHorizontal: 8,
    paddingVertical: 2,
    backgroundColor: '#e3f2fd',
    borderRadius: 4,
  },
  routeStats: {
    fontSize: 10,
    fontWeight: '500',
    color: '#1976d2',
    textAlign: 'center',
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 2,
  },
  locationDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  locationText: {
    fontSize: 11,
    color: '#333',
    flex: 1,
  },
  routeLine: {
    width: 2,
    height: 16,
    backgroundColor: '#ddd',
    marginLeft: 3,
    marginVertical: 2,
  },
  detailsContainer: {
    flex: 1,
    gap: 6,
    justifyContent: 'flex-start',
    paddingRight: 8,
    paddingLeft: 4,
  },
  dateTimeContainer: {
    alignItems: 'flex-start',
  },
  dateText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  timeText: {
    fontSize: 14,
    color: '#666',
  },
  communitiesContainer: {
    gap: 4,
    marginBottom: 8,
  },
  sectionLabel: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 4,
    alignItems: 'flex-start',
    justifyContent: 'flex-start',
    width: '100%',
  },
  communityChip: {
    backgroundColor: '#f0f4f8',
    height: 26,
    marginBottom: 3,
    marginRight: 4,
    borderRadius: 13,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#d1d9e0',
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
    alignSelf: 'flex-start',
  },
  chipText: {
    fontSize: 10,
    lineHeight: 14,
    fontWeight: '600',
    color: '#2d3748',
    textAlign: 'center',
    includeFontPadding: false,
  },
  estimatesContainer: {
    gap: 4,
  },
  estimateItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  estimateLabel: {
    fontSize: 12,
    color: '#666',
  },
  estimateValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  estimateDisclaimer: {
    fontSize: 10,
    color: '#999',
    fontStyle: 'italic',
    marginTop: 4,
  },
  creatorText: {
    fontSize: 11,
    color: '#999',
    fontStyle: 'italic',
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  actionButton: {
    flex: 1,
    borderRadius: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  leaveButton: {
    backgroundColor: '#FF5722',
  },
  messageButton: {
    flex: 1,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2196F3',
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
  },
  deleteButton: {
    flex: 1,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#d32f2f',
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
  },
  buttonContent: {
    height: 40,
    paddingHorizontal: 8,
  },
});