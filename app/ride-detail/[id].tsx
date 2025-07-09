import React, { useState, useEffect } from 'react';
import { 
  View, 
  StyleSheet, 
  ScrollView, 
  Alert,
  SafeAreaView 
} from 'react-native';
import { 
  Text, 
  Button, 
  Card, 
  IconButton, 
  Chip,
  Divider
} from 'react-native-paper';
import { useLocalSearchParams, router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://172.28.119.64:8000';

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

interface RideDetail {
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

export default function RideDetailScreen() {
  const { id } = useLocalSearchParams();
  const [ride, setRide] = useState<RideDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentUserEmail, setCurrentUserEmail] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchRideDetail();
      getCurrentUserEmail();
    }
  }, [id]);

  const getCurrentUserEmail = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        const user = JSON.parse(userData);
        setCurrentUserEmail(user.email);
      }
    } catch (error) {
      console.error('Error getting user email:', error);
    }
  };

  const fetchRideDetail = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride-request/${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRide(data);
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to load ride details');
      }
    } catch (error) {
      console.error('Error fetching ride detail:', error);
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setLoading(false);
    }
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
      weekday: 'long',
      year: 'numeric',
      month: 'long',
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

  const isUserJoined = () => {
    return currentUserEmail && ride && ride.user_ids.includes(currentUserEmail);
  };

  const isUserCreator = () => {
    return currentUserEmail && ride && ride.creator_email === currentUserEmail;
  };

  const leaveRide = async () => {
    if (!ride) return;

    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride-request/${ride._id}/leave`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        Alert.alert('Success', 'You have left the ride', [
          {
            text: 'OK',
            onPress: () => router.back()
          }
        ]);
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to leave ride');
      }
    } catch (error) {
      console.error('Error leaving ride:', error);
      Alert.alert('Error', 'Unable to connect to server');
    }
  };

  const deleteRide = async () => {
    if (!ride) return;

    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride-request/${ride._id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        Alert.alert('Success', 'Ride deleted successfully', [
          {
            text: 'OK',
            onPress: () => router.back()
          }
        ]);
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to delete ride');
      }
    } catch (error) {
      console.error('Error deleting ride:', error);
      Alert.alert('Error', 'Unable to delete ride');
    }
  };

  const handleDeleteRide = () => {
    Alert.alert(
      'Delete Ride',
      'Are you sure you want to delete this ride? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive', 
          onPress: deleteRide 
        }
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text>Loading ride details...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!ride) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text>Ride not found</Text>
          <Button onPress={() => router.back()}>Go Back</Button>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <IconButton 
            icon="arrow-left" 
            size={24} 
            onPress={() => router.back()}
          />
          <Text style={styles.headerTitle}>Ride Details</Text>
          <View style={styles.headerSpacer} />
        </View>

        {/* Route Card */}
        <Card style={styles.card}>
          <Card.Content>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Route</Text>
              {ride.route_info && (
                <View style={styles.routeStatsContainer}>
                  <Text style={styles.routeStats}>
                    {ride.route_info.formatted_distance} • {ride.route_info.formatted_duration}
                  </Text>
                </View>
              )}
            </View>
            <View style={styles.routeContainer}>
              <View style={styles.locationRow}>
                <View style={[styles.locationDot, { backgroundColor: '#4CAF50' }]} />
                <Text style={styles.locationText}>{ride.origin.description}</Text>
              </View>
              <View style={styles.routeLine} />
              <View style={styles.locationRow}>
                <View style={[styles.locationDot, { backgroundColor: '#F44336' }]} />
                <Text style={styles.locationText}>{ride.destination.description}</Text>
              </View>
            </View>
          </Card.Content>
        </Card>

        {/* Date & Time Card */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Date & Time</Text>
            <Text style={styles.dateText}>{formatDate(ride.departure_date)}</Text>
            <Text style={styles.timeText}>
              {formatTime(ride.earliest_time)} - {formatTime(ride.latest_time)}
            </Text>
          </Card.Content>
        </Card>

        {/* Communities Card */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Communities</Text>
            <View style={styles.chipContainer}>
              {ride.communities.map((community, index) => (
                <Chip key={index} style={styles.communityChip} textStyle={styles.chipText}>
                  {community}
                </Chip>
              ))}
            </View>
          </Card.Content>
        </Card>

        {/* Trip Info Card */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Trip Information</Text>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Available spots:</Text>
              <Text style={styles.infoValue}>{ride.available_spots}/{ride.max_participants}</Text>
            </View>

            {ride.estimated_travel_time && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Estimated travel time:</Text>
                <Text style={styles.infoValue}>{formatTravelTime(ride.estimated_travel_time)}</Text>
              </View>
            )}

            {ride.estimated_total_price && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Estimated total price:</Text>
                <Text style={styles.infoValue}>${ride.estimated_total_price.toFixed(2)}</Text>
              </View>
            )}

            {ride.creator_name && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Posted by:</Text>
                <Text style={styles.infoValue}>{ride.creator_name}</Text>
              </View>
            )}

            {(ride.estimated_travel_time || ride.estimated_total_price) && (
              <Text style={styles.disclaimer}>
                * Estimates provided by Uber API
              </Text>
            )}
          </Card.Content>
        </Card>

        {/* Action Buttons */}
        <View style={styles.actionContainer}>
          {isUserJoined() && (
            <Button
              mode="contained"
              onPress={leaveRide}
              style={styles.leaveButton}
              buttonColor="#FF5252"
              textColor="#FFFFFF"
            >
              Leave Ride
            </Button>
          )}
          
          {isUserCreator() && (
            <Button
              mode="outlined"
              onPress={handleDeleteRide}
              style={styles.deleteButton}
              buttonColor="#ffebee"
              textColor="#d32f2f"
              icon="delete"
            >
              Delete Ride
            </Button>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 8,
    backgroundColor: '#fff',
    elevation: 2,
  },
  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#333',
  },
  headerSpacer: {
    width: 48,
  },
  card: {
    margin: 16,
    marginBottom: 8,
    elevation: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  routeStatsContainer: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#e3f2fd',
    borderRadius: 6,
  },
  routeStats: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1976d2',
  },
  routeContainer: {
    paddingVertical: 8,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  locationDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  locationText: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  routeLine: {
    width: 2,
    height: 20,
    backgroundColor: '#ddd',
    marginLeft: 5,
    marginVertical: 4,
  },
  dateText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  timeText: {
    fontSize: 16,
    color: '#666',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  communityChip: {
    backgroundColor: '#e3f2fd',
  },
  chipText: {
    fontSize: 12,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  disclaimer: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
    marginTop: 8,
  },
  actionContainer: {
    margin: 16,
    marginTop: 8,
  },
  leaveButton: {
    paddingVertical: 4,
    marginBottom: 12,
  },
  deleteButton: {
    paddingVertical: 4,
    borderColor: '#d32f2f',
  },
});