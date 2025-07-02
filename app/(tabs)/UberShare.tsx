import 'react-native-get-random-values';
import React, { useState, useEffect } from 'react';
import { Menu, Button as RNButton, IconButton } from 'react-native-paper';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as Location from 'expo-location';
import LocationInput from '@/components/LocationInput';

// should be replaced with list of local universities
const COMMUNITY_OPTIONS = ['Pomona', 'Harvey Mudd', 'Scripps', 'Pitzer', 'CMC', '5C'];

interface LocationData {
  description: string;
  latitude?: number;
  longitude?: number;
}

export default function ShareScreen() {
  const [whereFrom, setWhereFrom] = useState<LocationData>({ description: '' });
  const [whereTo, setWhereTo] = useState<LocationData>({ description: '' });
  const [when, setWhen] = useState(new Date());
  const [waitTime, setWaitTime] = useState('');
  const [waitMenuVisible, setWaitMenuVisible] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedCommunities, setSelectedCommunities] = useState<string[]>([]);
  const [currentLocation, setCurrentLocation] = useState<Location.LocationObject | null>(null);

  useEffect(() => {
    getCurrentLocation();
  }, []);

  const getCurrentLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied', 'Location permission is required for this feature.');
        return;
      }

      const location = await Location.getCurrentPositionAsync({});
      setCurrentLocation(location);
    } catch (error) {
      console.error('Error getting location:', error);
    }
  };

  const setCurrentLocationAsSelected = async (isFrom: boolean) => {
    if (!currentLocation) {
      await getCurrentLocation();
    }
    
    if (!currentLocation) {
      Alert.alert('Location unavailable', 'Please enable location services.');
      return;
    }

    const locationData: LocationData = {
      description: 'Current Location',
      latitude: currentLocation.coords.latitude,
      longitude: currentLocation.coords.longitude,
    };

    if (isFrom) {
      setWhereFrom(locationData);
    } else {
      setWhereTo(locationData);
    }
  };

  const toggleCommunity = (community: string) => {
    setSelectedCommunities((prev) =>
      prev.includes(community)
        ? prev.filter((c) => c !== community)
        : [...prev, community]
    );
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Uber Share</Text>
      
      {/* Where From */}
      <LocationInput
        placeholder="Where from?"
        value={whereFrom}
        onLocationSelect={setWhereFrom}
        onCurrentLocation={() => setCurrentLocationAsSelected(true)}
        useAutocomplete={true}
      />

      {/* Where To */}
      <LocationInput
        placeholder="Where to?"
        value={whereTo}
        onLocationSelect={setWhereTo}
        onCurrentLocation={() => setCurrentLocationAsSelected(false)}
        useAutocomplete={true}
      />

      {/* When */}
      <TouchableOpacity
        style={styles.input}
        onPress={() => setShowDatePicker(true)}
      >
        <Text style={styles.placeholderText}>
          {when.toLocaleString()}
        </Text>
      </TouchableOpacity>
      {showDatePicker && (
        <DateTimePicker
          value={when}
          mode="datetime"
          display="default"
          onChange={(_, date) => {
            if (date) setWhen(date);
            setShowDatePicker(false);
          }}
        />
      )}

      {/* Wait Time */}
      <Menu
        visible={waitMenuVisible}
        onDismiss={() => setWaitMenuVisible(false)}
        anchor={
          <RNButton
            mode="outlined"
            onPress={() => setWaitMenuVisible(true)}
            style={styles.menuButton}
          >
            {waitTime ? `Wait ${waitTime} min` : 'Select wait time'}
          </RNButton>
        }
      >
        {[0, 5, 10, 15, 20, 25, 30, 45, 60, "+"].map((min) => (
          <Menu.Item
            key={min}
            onPress={() => {
              setWaitTime(min.toString());
              setWaitMenuVisible(false);
            }}
            title={`${min} min`}
          />
        ))}
      </Menu>

      {/* Community */}
      <View style={styles.communityContainer}>
        {COMMUNITY_OPTIONS.map((community) => (
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
              {community}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity 
        style={styles.doneButton} 
        onPress={() => {
          console.log('Ride Details:', {
            from: whereFrom,
            to: whereTo,
            when: when,
            waitTime: waitTime,
            communities: selectedCommunities
          });
        }}
      >
        <Text style={{ color: 'white', fontWeight: 'bold' }}>Share Ride</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    gap: 16,
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
  menuButton: {
    marginBottom: 16,
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
  doneButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 30,
    marginTop: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    marginTop: 70,
  },
});