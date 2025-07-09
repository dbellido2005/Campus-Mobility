import React from 'react';
import { View, StyleSheet } from 'react-native';
import HomeContent from '@/components/HomeContent';

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <HomeContent />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
