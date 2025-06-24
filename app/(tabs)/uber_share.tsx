import React, { useState } from 'react';
import { Menu, Button as RNButton } from 'react-native-paper';
import {
  View,
  Text,
  TextInput,
  Button,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';

// should be replaced with list of local universities
const COMMUNITY_OPTIONS = ['Pomona', 'Harvey Mudd', 'Scripps', 'Pitzer', 'CMC', '5C'];

export default function ShareScreen() {
  const [where, setWhere] = useState('');
  const [when, setWhen] = useState(new Date());
  const [waitTime, setWaitTime] = useState('');
  const [waitMenuVisible, setWaitMenuVisible] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedCommunities, setSelectedCommunities] = useState<string[]>([]);
  

  const toggleCommunity = (community: string) => {
    setSelectedCommunities((prev) =>
      prev.includes(community)
        ? prev.filter((c) => c !== community)
        : [...prev, community]
    );
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Share Uber</Text>
      <Text style={styles.label}>Where to?</Text>
      <TextInput
        style={styles.input}
        placeholder="Enter destination"
        value={where}
        onChangeText={setWhere}
      />

      <Text style={styles.label}>When?</Text>
      <TouchableOpacity
        style={styles.input}
        onPress={() => setShowDatePicker(true)}
      >
        <Text>{when.toLocaleString()}</Text>
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

    <Text style={styles.label}>Wait Time (minutes)</Text>
    <Menu
        visible={waitMenuVisible}
        onDismiss={() => setWaitMenuVisible(false)}
        anchor={
            <RNButton
            mode="outlined"
            onPress={() => setWaitMenuVisible(true)}
            style={{ marginBottom: 16 }}
            >
            {waitTime ? `${waitTime} min` : 'Select wait time...'}
            </RNButton>
        }
        >
        {[0, 5, 10, 15, 20, 25, 30, 45, 60, "+"].map((min) => (
            <Menu.Item
            key={min}
            onPress={() => {
                setWaitTime(min.toString());
                setWaitMenuVisible(false);
                console.log('waitTime:', min);
            }}
            title={`${min} min`}
            />
        ))}
    </Menu>

    
      <Text style={styles.label}>Community</Text>
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

      <TouchableOpacity style={styles.doneButton} onPress={() => console.log('Submitted')}>
        <Text style={{ color: 'white', fontWeight: 'bold' }}>Done</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    gap: 16,
  },
  label: {
    fontWeight: '600',
    fontSize: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#fff',
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
