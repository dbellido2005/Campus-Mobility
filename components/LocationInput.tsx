import 'react-native-get-random-values';
import React, { useState, useRef, useEffect } from 'react';
import { View, TextInput, StyleSheet } from 'react-native';
import { IconButton } from 'react-native-paper';
import { GooglePlacesAutocomplete } from 'react-native-google-places-autocomplete';

const GOOGLE_PLACES_API_KEY = 'AIzaSyAfLzp1VqK5YdO5wIgQSAaC9XCp_aj7zeo';

interface LocationData {
  description: string;
  latitude?: number;
  longitude?: number;
}

interface LocationInputProps {
  placeholder: string;
  value: LocationData;
  onLocationSelect: (location: LocationData) => void;
  onCurrentLocation: () => void;
  useAutocomplete?: boolean;
}

export default function LocationInput({
  placeholder,
  value,
  onLocationSelect,
  onCurrentLocation,
  useAutocomplete = false,
}: LocationInputProps) {
  const [inputValue, setInputValue] = useState(value.description);
  const [hasError, setHasError] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Add a small delay to ensure proper initialization
    const timer = setTimeout(() => setIsInitialized(true), 100);
    return () => clearTimeout(timer);
  }, []);
  const autocompleteRef = useRef<any>(null);

  // Sync inputValue with value prop
  useEffect(() => {
    setInputValue(value.description);
  }, [value.description]);

  // Try autocomplete, fallback to TextInput if there are issues
  if (useAutocomplete && GOOGLE_PLACES_API_KEY && !hasError && isInitialized) {
    return (
      <View style={styles.container}>
        <GooglePlacesAutocomplete
          ref={autocompleteRef}
          placeholder={placeholder}
          onPress={(data, details = null) => {
            try {
              const location: LocationData = {
                description: data.description,
                latitude: details?.geometry?.location?.lat,
                longitude: details?.geometry?.location?.lng,
              };
              onLocationSelect(location);
            } catch (error) {
              console.error('Error processing location selection:', error);
              setHasError(true);
            }
          }}
          query={{
            key: GOOGLE_PLACES_API_KEY,
            language: 'en',
          }}
          fetchDetails={true}
          enablePoweredByContainer={false}
          suppressDefaultStyles
          textInputProps={{
            autoCorrect: false,
            onFocus: () => {},
            onBlur: () => {},
          }}
          styles={{
            container: {
              flex: 1,
            },
            textInputContainer: {
              borderWidth: 1,
              borderColor: '#ccc',
              borderRadius: 12,
              backgroundColor: '#fff',
            },
            textInput: {
              height: 45,
              fontSize: 16,
              paddingHorizontal: 12,
              paddingRight: 40,
            },
            listView: {
              backgroundColor: '#fff',
              borderWidth: 1,
              borderColor: '#ccc',
              borderTopWidth: 0,
              borderBottomLeftRadius: 12,
              borderBottomRightRadius: 12,
              maxHeight: 200,
              position: 'absolute',
              top: 45,
              left: 0,
              right: 0,
              zIndex: 1000,
            },
          }}
          onFail={(error) => {
            console.log('GooglePlacesAutocomplete error:', error);
            setHasError(true);
          }}
          predefinedPlaces={[]}
          listEmptyComponent={null}
        />
        <IconButton
          icon="crosshairs-gps"
          size={20}
          onPress={onCurrentLocation}
          style={styles.locationButton}
        />
      </View>
    );
  }

  // Fallback to regular TextInput - works reliably
  return (
    <View style={styles.container}>
      <TextInput
        style={styles.textInput}
        placeholder={placeholder}
        value={inputValue}
        onChangeText={(text) => {
          setInputValue(text);
          onLocationSelect({ description: text });
        }}
        autoCorrect={false}
        autoCapitalize="words"
      />
      <IconButton
        icon="crosshairs-gps"
        size={20}
        onPress={onCurrentLocation}
        style={styles.locationButton}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    position: 'relative',
    marginBottom: 16,
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#fff',
    fontSize: 16,
    paddingRight: 40,
  },
  locationButton: {
    position: 'absolute',
    right: 5,
    top: 2,
    zIndex: 10,
  },
});