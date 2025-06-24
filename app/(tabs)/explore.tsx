import React, { useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import RNPickerSelect from 'react-native-picker-select';

export default function TestDropdown() {
  const [waitTime, setWaitTime] = useState('');

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Wait Time (minutes)</Text>
      <RNPickerSelect
        onValueChange={(value) => {
          setWaitTime(value);
          console.log('Selected:', value);
        }}
        placeholder={{ label: 'Select wait time...', value: null }}
        value={waitTime}
        useNativeAndroidPickerStyle={false}
        style={{
          inputIOS: styles.input,
          inputAndroid: styles.input,
        }}
        items={[
          { label: '0 min', value: '0' },
          { label: '5 min', value: '5' },
          { label: '10 min', value: '10' },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 100,
    padding: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  input: {
    fontSize: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 12,
    backgroundColor: '#fff',
    color: 'black',
  },
});
