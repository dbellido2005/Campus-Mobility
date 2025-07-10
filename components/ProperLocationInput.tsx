import React, { useState, useEffect } from 'react';
import { View, TextInput, StyleSheet, FlatList, TouchableOpacity, Text } from 'react-native';
import { IconButton } from 'react-native-paper';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface LocationData {
  description: string;
  latitude?: number;
  longitude?: number;
}

interface Suggestion {
  place_id: string;
  description: string;
}

interface ProperLocationInputProps {
  placeholder: string;
  value: LocationData;
  onLocationSelect: (location: LocationData) => void;
  onCurrentLocation: () => void;
}

export default function ProperLocationInput({
  placeholder,
  value,
  onLocationSelect,
  onCurrentLocation,
}: ProperLocationInputProps) {
  const [inputValue, setInputValue] = useState(value.description);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setInputValue(value.description);
  }, [value.description]);

  const searchPlaces = async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/places/autocomplete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();

      if (response.ok && data.suggestions) {
        setSuggestions(data.suggestions);
        setShowSuggestions(data.suggestions.length > 0);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (error) {
      console.error('Error fetching places:', error);
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextChange = (text: string) => {
    setInputValue(text);
    onLocationSelect({ description: text });
    
    // Debounce the API call
    setTimeout(() => {
      searchPlaces(text);
    }, 300);
  };

  const selectSuggestion = async (suggestion: Suggestion) => {
    setInputValue(suggestion.description);
    setShowSuggestions(false);
    setSuggestions([]);

    try {
      // Get detailed place information including coordinates
      const response = await fetch(`${API_BASE_URL}/places/details`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ place_id: suggestion.place_id }),
      });

      const data = await response.json();

      if (response.ok && data.location) {
        const location: LocationData = {
          description: suggestion.description,
          latitude: data.location.latitude,
          longitude: data.location.longitude,
        };
        onLocationSelect(location);
      } else {
        // Fallback without coordinates
        onLocationSelect({ description: suggestion.description });
      }
    } catch (error) {
      console.error('Error getting place details:', error);
      // Fallback without coordinates
      onLocationSelect({ description: suggestion.description });
    }
  };

  const renderSuggestion = ({ item }: { item: Suggestion }) => (
    <TouchableOpacity
      style={styles.suggestionItem}
      onPress={() => selectSuggestion(item)}
    >
      <Text style={styles.suggestionText}>{item.description}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          placeholder={placeholder}
          value={inputValue}
          onChangeText={handleTextChange}
          onFocus={() => {
            if (suggestions.length > 0) setShowSuggestions(true);
          }}
          onBlur={() => {
            // Delay hiding suggestions to allow for selection
            setTimeout(() => setShowSuggestions(false), 150);
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
      
      {showSuggestions && (
        <View style={styles.suggestionsContainer}>
          <FlatList
            data={suggestions}
            renderItem={renderSuggestion}
            keyExtractor={(item) => item.place_id}
            style={styles.suggestionsList}
            keyboardShouldPersistTaps="handled"
            nestedScrollEnabled={true}
          />
        </View>
      )}
      
      {isLoading && (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Searching...</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
    zIndex: 1000, // High z-index to appear above other content
    elevation: 1000, // Android elevation
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    position: 'relative',
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#f5f5f5',
    fontSize: 16,
    paddingRight: 40,
    zIndex: 1,
  },
  locationButton: {
    position: 'absolute',
    right: 5,
    top: 2,
    zIndex: 10,
  },
  suggestionsContainer: {
    position: 'absolute',
    top: 45,
    left: 0,
    right: 0,
    zIndex: 10000, // Very high z-index
    elevation: 10000, // Very high Android elevation
  },
  suggestionsList: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderTopWidth: 0,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 12,
    maxHeight: 200,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  suggestionItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  suggestionText: {
    fontSize: 16,
    color: '#333',
  },
  loadingContainer: {
    position: 'absolute',
    top: 45,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderTopWidth: 0,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 12,
    padding: 12,
    zIndex: 10000,
    elevation: 10000,
  },
  loadingText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});