import React, { useEffect, useState } from 'react';
import { View, Text, Button, StyleSheet, Alert } from 'react-native';

export default function FindDrivers() {
  const [message, setMessage] = useState("Loading...");
  const [isLoading, setIsLoading] = useState(false);

  const testConnection = async (url: string) => {
    setIsLoading(true);
    setMessage(`Testing connection to ${url}...`);
    
    try {
      console.log(`Attempting to fetch from: ${url}`);
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      console.log(`Response status: ${response.status}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      setMessage(`✅ Success: ${data.message || JSON.stringify(data)}`);
    } catch (error) {
      console.error('Network error:', error);
      setMessage(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    testConnection("http://172.28.119.64:8000/ping");
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Find Drivers</Text>
      <Text style={styles.message}>{message}</Text>
      
      <View style={styles.buttonContainer}>
        <Button
          title="Test Local IP"
          onPress={() => testConnection("http://172.28.119.64:8000/ping")}
          disabled={isLoading}
        />
        <Button
          title="Test Localhost"
          onPress={() => testConnection("http://127.0.0.1:8000/ping")}
          disabled={isLoading}
        />
        <Button
          title="Test Local Network"
          onPress={() => testConnection("http://172.28.119.64:8000/ping")}
          disabled={isLoading}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  message: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 30,
    paddingHorizontal: 20,
  },
  buttonContainer: {
    gap: 10,
    width: '100%',
  },
});
