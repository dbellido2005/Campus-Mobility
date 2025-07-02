import React, { useState, useEffect } from 'react';
import { View, TextInput, StyleSheet, FlatList, TouchableOpacity, Text } from 'react-native';
import { IconButton } from 'react-native-paper';

interface LocationData {
  description: string;
  latitude?: number;
  longitude?: number;
}

interface SimpleLocationInputProps {
  placeholder: string;
  value: LocationData;
  onLocationSelect: (location: LocationData) => void;
  onCurrentLocation: () => void;
}

// Common locations around Claremont Colleges for quick suggestions
const COMMON_LOCATIONS = [
  'Claremont, CA',
  'Pomona College, Claremont, CA',
  'Harvey Mudd College, Claremont, CA',
  'Scripps College, Claremont, CA',
  'Pitzer College, Claremont, CA',
  'Claremont McKenna College, Claremont, CA',
  'Claremont Village, Claremont, CA',
  'LAX Airport, Los Angeles, CA',
  'Union Station, Los Angeles, CA',
  'Ontario Airport, Ontario, CA',
  'Los Angeles, CA',
  'Santa Monica, CA',
  'Beverly Hills, CA',
  'Hollywood, CA',
  'Pasadena, CA',
  'Disneyland, Anaheim, CA',
  'USC, Los Angeles, CA',
  'UCLA, Los Angeles, CA',
  'Downtown LA, Los Angeles, CA',
  'Westwood, Los Angeles, CA',
];

export default function SimpleLocationInput({
  placeholder,
  value,
  onLocationSelect,
  onCurrentLocation,
}: SimpleLocationInputProps) {
  const [inputValue, setInputValue] = useState(value.description);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    setInputValue(value.description);
  }, [value.description]);

  const handleTextChange = (text: string) => {
    setInputValue(text);
    onLocationSelect({ description: text });

    // Filter suggestions based on input
    if (text.length > 1) {
      const filtered = COMMON_LOCATIONS.filter(location =>
        location.toLowerCase().includes(text.toLowerCase())
      ).slice(0, 5); // Limit to 5 suggestions
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const selectSuggestion = (suggestion: string) => {
    setInputValue(suggestion);
    onLocationSelect({ description: suggestion });
    setShowSuggestions(false);
    setSuggestions([]);
  };

  const renderSuggestion = ({ item }: { item: string }) => (
    <TouchableOpacity
      style={styles.suggestionItem}
      onPress={() => selectSuggestion(item)}
    >
      <Text style={styles.suggestionText}>{item}</Text>
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
            keyExtractor={(item, index) => `suggestion-${index}`}
            style={styles.suggestionsList}
            keyboardShouldPersistTaps="handled"
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
    zIndex: 1,
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
  suggestionsContainer: {
    position: 'absolute',
    top: 45,
    left: 0,
    right: 0,
    zIndex: 1000,
  },
  suggestionsList: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderTopWidth: 0,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 12,
    maxHeight: 200,
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
});