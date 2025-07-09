import React, { useState, useEffect } from 'react';
import { 
  View, 
  StyleSheet, 
  ScrollView, 
  Alert, 
  TouchableOpacity,
  RefreshControl 
} from 'react-native';
import { 
  Text, 
  TextInput, 
  Button, 
  Card, 
  IconButton, 
  Divider,
  Portal,
  Modal
} from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router, useFocusEffect } from 'expo-router';
import { useCallback } from 'react';
import ProfilePicture from './ProfilePicture';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface FrequentRider {
  user_email: string;
  user_name?: string;
  ride_count: number;
}

interface FrequentDestination {
  destination: string;
  trip_count: number;
}

interface UberShareStats {
  times_uber_share_last_month: number;
  most_frequent_riders: FrequentRider[];
  most_frequent_destinations: FrequentDestination[];
  stats_last_updated?: string;
}

interface PlannedTrip {
  _id: string;
  origin?: {
    description: string;
    latitude?: number;
    longitude?: number;
  };
  destination?: {
    description: string;
    latitude?: number;
    longitude?: number;
  };
  departure_date: string;
  earliest_time: number;
  latest_time: number;
  creator_email: string;
  creator_name?: string;
  max_participants: number;
  available_spots: number;
  status: string;
  user_ids: string[];
  communities: string[];
  estimated_total_price?: number;
  estimated_travel_time?: number;
}

interface UserProfile {
  name?: string;
  firstName?: string;
  lastName?: string;
  email: string;
  college: string;
  year?: string;
  major?: string;
  bio?: string;
  profile_picture?: string;
  created_at: string;
  uber_share_stats: UberShareStats;
}

const YEAR_OPTIONS = ['Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate'];

interface ProfileScreenProps {
  onLogout?: () => void;
}

export default function ProfileScreen({ onLogout }: ProfileScreenProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [plannedTrips, setPlannedTrips] = useState<PlannedTrip[]>([]);
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    firstName: '',
    lastName: '',
    year: '',
    major: '',
    bio: ''
  });

  const [showYearModal, setShowYearModal] = useState(false);

  useEffect(() => {
    fetchProfile();
    fetchPlannedTrips();
  }, []);

  // Refresh planned trips when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      console.log('Profile screen focused, refreshing planned trips');
      fetchPlannedTrips();
    }, [])
  );

  const fetchProfile = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setEditForm({
          firstName: data.firstName || data.name?.split(' ')[0] || '',
          lastName: data.lastName || data.name?.split(' ').slice(1).join(' ') || '',
          year: data.year || '',
          major: data.major || '',
          bio: data.bio || ''
        });
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to load profile');
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchPlannedTrips = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        console.log('No token found for planned trips');
        return;
      }

      console.log('Fetching planned trips from:', `${API_BASE_URL}/my-rides`);
      const response = await fetch(`${API_BASE_URL}/my-rides`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Planned trips response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Planned trips data received:', data.length, 'rides');
        setPlannedTrips(data);
      } else {
        const errorText = await response.text();
        console.error('Failed to fetch planned trips, status:', response.status, 'error:', errorText);
      }
    } catch (error) {
      console.error('Error fetching planned trips:', error);
    }
  };

  const updateProfile = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      // Only send non-empty fields
      const updateData: any = {};
      if (editForm.firstName.trim()) updateData.firstName = editForm.firstName.trim();
      if (editForm.lastName.trim()) updateData.lastName = editForm.lastName.trim();
      if (editForm.year) updateData.year = editForm.year;
      if (editForm.major.trim()) updateData.major = editForm.major.trim();
      if (editForm.bio.trim()) updateData.bio = editForm.bio.trim();

      const response = await fetch(`${API_BASE_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        const updatedProfile = await response.json();
        setProfile(updatedProfile);
        setEditing(false);
        Alert.alert('Success', 'Profile updated successfully!');
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', 'Unable to connect to server');
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchProfile();
    fetchPlannedTrips();
  };

  const handleProfilePictureUpdate = (newImageData: string) => {
    if (profile) {
      setProfile({
        ...profile,
        profile_picture: newImageData
      });
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              if (onLogout) {
                await onLogout();
                Alert.alert('Success', 'Logged out successfully');
              } else {
                // Fallback to original logic if no onLogout prop
                await AsyncStorage.removeItem('userToken');
                await AsyncStorage.removeItem('user');
                Alert.alert('Success', 'Logged out successfully');
              }
            } catch (error) {
              console.error('Error logging out:', error);
            }
          }
        }
      ]
    );
  };

  const handleDeleteAccount = async () => {
    Alert.alert(
      'Delete Account',
      'Are you sure you want to permanently delete your account? This action cannot be undone and will remove all your data.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              const token = await AsyncStorage.getItem('userToken');
              if (!token) {
                Alert.alert('Error', 'Please login again');
                return;
              }

              const response = await fetch(`${API_BASE_URL}/delete-account`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                }
              });

              if (response.ok) {
                // Clear local storage
                await AsyncStorage.removeItem('userToken');
                await AsyncStorage.removeItem('user');
                
                Alert.alert('Success', 'Account deleted successfully', [
                  {
                    text: 'OK',
                    onPress: () => {
                      if (onLogout) {
                        onLogout();
                      }
                    }
                  }
                ]);
              } else {
                const error = await response.json();
                Alert.alert('Error', error.detail || 'Failed to delete account');
              }
            } catch (error) {
              console.error('Error deleting account:', error);
              Alert.alert('Error', 'Unable to connect to server');
            }
          }
        }
      ]
    );
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

  const renderPlannedTrips = () => {
    if (plannedTrips.length === 0) {
      return (
        <Card style={styles.detailCard}>
          <Card.Content>
            <Text style={styles.detailTitle}>Planned Trips</Text>
            <Text style={styles.noDataText}>No planned trips yet</Text>
          </Card.Content>
        </Card>
      );
    }

    return (
      <Card style={styles.detailCard}>
        <Card.Content>
          <Text style={styles.detailTitle}>Planned Trips</Text>
          {plannedTrips.slice(0, 3).map((trip) => {
            // Safe access to destination
            const destinationDescription = trip.destination?.description || 'Unknown destination';
            
            return (
              <TouchableOpacity
                key={trip._id}
                style={styles.tripRow}
                onPress={() => {
                  router.push(`/ride-detail/${trip._id}`);
                }}
              >
                <View style={styles.tripInfo}>
                  <Text style={styles.tripDestination} numberOfLines={1}>
                    {destinationDescription}
                  </Text>
                  <Text style={styles.tripDate}>
                    {formatDate(trip.departure_date)} • {formatTime(trip.earliest_time)}
                  </Text>
                </View>
                <IconButton icon="chevron-right" size={20} />
              </TouchableOpacity>
            );
          })}
          {plannedTrips.length > 3 && (
            <TouchableOpacity style={styles.viewAllTrips}>
              <Text style={styles.viewAllText}>View all {plannedTrips.length} trips</Text>
            </TouchableOpacity>
          )}
        </Card.Content>
      </Card>
    );
  };

  const renderUberShareCard = () => (
    <Card style={styles.statCard}>
      <Card.Content>
        <View style={styles.statHeader}>
          <Text style={styles.statIcon}>🚕</Text>
          <View style={styles.statMainInfo}>
            <Text style={styles.statValue}>{profile?.uber_share_stats.times_uber_share_last_month || 0}</Text>
            <Text style={styles.statTitle}>Uber Shares This Month</Text>
          </View>
        </View>
      </Card.Content>
    </Card>
  );

  const renderFrequentRiders = () => {
    const riders = profile?.uber_share_stats.most_frequent_riders || [];
    if (riders.length === 0) {
      return (
        <Card style={styles.detailCard}>
          <Card.Content>
            <Text style={styles.detailTitle}>Most Frequent Riders</Text>
            <Text style={styles.noDataText}>No frequent riders yet</Text>
          </Card.Content>
        </Card>
      );
    }

    return (
      <Card style={styles.detailCard}>
        <Card.Content>
          <Text style={styles.detailTitle}>Most Frequent Riders</Text>
          {riders.map((rider, index) => (
            <View key={rider.user_email} style={styles.itemRow}>
              <View style={styles.itemInfo}>
                <Text style={styles.itemPrimary}>
                  {rider.user_name || rider.user_email.split('@')[0]}
                </Text>
                <Text style={styles.itemSecondary}>{rider.user_email}</Text>
              </View>
              <View style={styles.itemCount}>
                <Text style={styles.countValue}>{rider.ride_count}</Text>
                <Text style={styles.countLabel}>rides</Text>
              </View>
            </View>
          ))}
        </Card.Content>
      </Card>
    );
  };

  const renderFrequentDestinations = () => {
    const destinations = profile?.uber_share_stats.most_frequent_destinations || [];
    if (destinations.length === 0) {
      return (
        <Card style={styles.detailCard}>
          <Card.Content>
            <Text style={styles.detailTitle}>Most Frequent Destinations</Text>
            <Text style={styles.noDataText}>No frequent destinations yet</Text>
          </Card.Content>
        </Card>
      );
    }

    return (
      <Card style={styles.detailCard}>
        <Card.Content>
          <Text style={styles.detailTitle}>Most Frequent Destinations</Text>
          {destinations.map((dest, index) => (
            <View key={index} style={styles.itemRow}>
              <View style={styles.itemInfo}>
                <Text style={styles.itemPrimary}>{dest.destination}</Text>
              </View>
              <View style={styles.itemCount}>
                <Text style={styles.countValue}>{dest.trip_count}</Text>
                <Text style={styles.countLabel}>trips</Text>
              </View>
            </View>
          ))}
        </Card.Content>
      </Card>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading profile...</Text>
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={styles.errorContainer}>
        <Text>Unable to load profile</Text>
        <Button onPress={fetchProfile}>Retry</Button>
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <Text style={styles.headerTitle}>Your Profile</Text>
          <View style={styles.headerActions}>
            <IconButton
              icon={editing ? "close" : "pencil"}
              size={24}
              onPress={() => {
                if (editing) {
                  setEditForm({
                    firstName: profile.firstName || profile.name?.split(' ')[0] || '',
                    lastName: profile.lastName || profile.name?.split(' ').slice(1).join(' ') || '',
                    year: profile.year || '',
                    major: profile.major || '',
                    bio: profile.bio || ''
                  });
                }
                setEditing(!editing);
              }}
            />
            <IconButton
              icon="logout"
              size={24}
              onPress={handleLogout}
            />
          </View>
        </View>
      </View>

      {/* Profile Card */}
      <Card style={styles.profileCard}>
        <Card.Content>
          <View style={styles.profileHeader}>
            <ProfilePicture
              profilePicture={profile.profile_picture}
              name={profile.firstName && profile.lastName ? `${profile.firstName} ${profile.lastName}` : profile.name}
              email={profile.email}
              size={80}
              editable={true}
              onImageUpdate={handleProfilePictureUpdate}
            />
            <View style={styles.profileInfo}>
              {editing ? (
                <View style={styles.nameEditContainer}>
                  <TextInput
                    mode="outlined"
                    value={editForm.firstName}
                    onChangeText={(text) => setEditForm({...editForm, firstName: text})}
                    placeholder="First name"
                    style={[styles.textInput, styles.nameInput]}
                  />
                  <TextInput
                    mode="outlined"
                    value={editForm.lastName}
                    onChangeText={(text) => setEditForm({...editForm, lastName: text})}
                    placeholder="Last name"
                    style={[styles.textInput, styles.nameInput]}
                  />
                </View>
              ) : (
                <Text style={styles.fullName}>
                  {profile.firstName && profile.lastName 
                    ? `${profile.firstName} ${profile.lastName}` 
                    : profile.name || 'Set your name'}
                </Text>
              )}
              <Text style={styles.collegeName}>{profile.college}</Text>
            </View>
          </View>

          <Divider style={styles.divider} />

          {/* Editable Fields */}
          <View style={styles.fieldsContainer}>
            {/* Year */
            <View style={styles.fieldContainer}>
              <Text style={styles.fieldLabel}>Year</Text>
              {editing ? (
                <TouchableOpacity 
                  style={[styles.yearSelector, { flex: 2 }]}
                  onPress={() => setShowYearModal(true)}
                >
                  <Text style={styles.yearSelectorText}>
                    {editForm.year || 'Select your year'}
                  </Text>
                  <IconButton icon="chevron-down" size={20} />
                </TouchableOpacity>
              ) : (
                <Text style={styles.fieldValue}>{profile.year || 'Not set'}</Text>
              )}
            </View>}

            {/* Major */}
            <View style={styles.fieldContainer}>
              <Text style={styles.fieldLabel}>Major</Text>
              {editing ? (
                <TextInput
                  mode="outlined"
                  value={editForm.major}
                  onChangeText={(text) => setEditForm({...editForm, major: text})}
                  placeholder="Enter your major"
                  style={[styles.textInput, { flex: 2 }]}
                />
              ) : (
                <Text style={styles.fieldValue}>{profile.major || 'Not set'}</Text>
              )}
            </View>

            {/* Bio */}
            <View style={[styles.fieldContainer, editing ? { alignItems: 'flex-start' } : {}]}>
              <Text style={styles.fieldLabel}>Bio</Text>
              {editing ? (
                <TextInput
                  mode="outlined"
                  value={editForm.bio}
                  onChangeText={(text) => setEditForm({...editForm, bio: text})}
                  placeholder="Tell us about yourself"
                  multiline
                  numberOfLines={3}
                  style={[styles.textInput, { flex: 2 }]}
                />
              ) : (
                <Text style={styles.fieldValue}>{profile.bio || 'Not set'}</Text>
              )}
            </View>
          </View>

          {editing && (
            <View style={styles.editActions}>
              <Button
                mode="outlined"
                onPress={() => {
                  setEditForm({
                    firstName: profile.firstName || profile.name?.split(' ')[0] || '',
                    lastName: profile.lastName || profile.name?.split(' ').slice(1).join(' ') || '',
                    year: profile.year || '',
                    major: profile.major || '',
                    bio: profile.bio || ''
                  });
                  setEditing(false);
                }}
                style={styles.cancelButton}
              >
                Cancel
              </Button>
              <Button
                mode="contained"
                onPress={updateProfile}
                style={styles.saveButton}
              >
                Save Changes
              </Button>
            </View>
          )}
        </Card.Content>
      </Card>

      {/* Uber Share Statistics */}
      <View style={styles.statsSection}>
        <Text style={styles.sectionTitle}>Uber Share Activity</Text>
        <Text style={styles.sectionSubtitle}>
          {profile.uber_share_stats.stats_last_updated 
            ? `Last updated: ${new Date(profile.uber_share_stats.stats_last_updated).toLocaleDateString()}`
            : 'Statistics will be available after your first Uber Share'
          }
        </Text>

        {renderUberShareCard()}
        {renderPlannedTrips()}
        {/* Temporarily hidden - keeping logic for later use */}
        {/* {renderFrequentRiders()}
        {renderFrequentDestinations()} */}
      </View>

      {/* Danger Zone */}
      <View style={styles.dangerZone}>
        <Text style={styles.dangerZoneTitle}>Danger Zone</Text>
        <Button
          mode="contained"
          onPress={handleDeleteAccount}
          style={styles.deleteButton}
          buttonColor="#FF5252"
          textColor="#FFFFFF"
          icon="delete"
        >
          Delete Account
        </Button>
        <Text style={styles.dangerZoneWarning}>
          This action cannot be undone. Your account and all associated data will be permanently deleted.
        </Text>
      </View>

      {/* Year Selection Modal */}
      <Portal>
        <Modal
          visible={showYearModal}
          onDismiss={() => setShowYearModal(false)}
          contentContainerStyle={styles.modalContainer}
        >
          <Text style={styles.modalTitle}>Select Your Year</Text>
          {YEAR_OPTIONS.map((year) => (
            <TouchableOpacity
              key={year}
              style={styles.yearOption}
              onPress={() => {
                setEditForm({...editForm, year});
                setShowYearModal(false);
              }}
            >
              <Text style={styles.yearOptionText}>{year}</Text>
            </TouchableOpacity>
          ))}
        </Modal>
      </Portal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    paddingBottom: 100, // Extra padding at bottom for tab navigation
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
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  headerActions: {
    flexDirection: 'row',
  },
  profileCard: {
    margin: 16,
    elevation: 4,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  profileInfo: {
    flex: 1,
    marginLeft: 16,
  },
  fullName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  collegeName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#666',
  },
  email: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  divider: {
    marginVertical: 16,
  },
  fieldsContainer: {
    gap: 16,
  },
  fieldContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  fieldLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  fieldValue: {
    fontSize: 16,
    color: '#666',
    flex: 2,
    textAlign: 'right',
  },
  textInput: {
    backgroundColor: '#fff',
  },
  nameEditContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 4,
  },
  nameInput: {
    flex: 1,
    height: 40,
  },
  yearSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#fff',
  },
  yearSelectorText: {
    fontSize: 16,
    color: '#333',
  },
  editActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
    gap: 12,
  },
  cancelButton: {
    flex: 1,
  },
  saveButton: {
    flex: 1,
  },
  statsSection: {
    margin: 16,
    marginTop: 0,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
  statCard: {
    elevation: 4,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statIcon: {
    fontSize: 32,
    marginRight: 16,
  },
  statMainInfo: {
    flex: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statTitle: {
    fontSize: 14,
    color: '#666',
  },
  detailCard: {
    elevation: 2,
    marginBottom: 12,
  },
  detailTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  noDataText: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  itemInfo: {
    flex: 1,
  },
  itemPrimary: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  itemSecondary: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  itemCount: {
    alignItems: 'center',
  },
  countValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FF9800',
  },
  countLabel: {
    fontSize: 12,
    color: '#666',
  },
  modalContainer: {
    backgroundColor: '#fff',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  yearOption: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#f0f0f0',
  },
  yearOptionText: {
    fontSize: 16,
    textAlign: 'center',
  },
  dangerZone: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#FFF5F5',
    borderWidth: 1,
    borderColor: '#FFCDD2',
  },
  dangerZoneTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#D32F2F',
    marginBottom: 12,
  },
  deleteButton: {
    marginBottom: 12,
  },
  dangerZoneWarning: {
    fontSize: 12,
    color: '#B71C1C',
    textAlign: 'center',
    lineHeight: 16,
  },
  tripRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  tripInfo: {
    flex: 1,
  },
  tripDestination: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 2,
  },
  tripDate: {
    fontSize: 12,
    color: '#666',
  },
  viewAllTrips: {
    paddingVertical: 12,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    marginTop: 8,
  },
  viewAllText: {
    fontSize: 14,
    color: '#2196F3',
    fontWeight: '500',
  },
});