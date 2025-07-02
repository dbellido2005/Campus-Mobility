import { Image } from 'expo-image';
import { StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';

import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

export default function HomeContent() {
  const router = useRouter();
  
  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#ffd966', dark: '#1D3D47' }}
      headerImage={
        <Image
          source={require('@/assets/images/gemini_logo3.jpg')}
          style={styles.reactLogo}
        />
      }>
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Where to next?</ThemedText>
      </ThemedView>
      <ThemedText>Share. Save. Connect</ThemedText>
      <ThemedView style={styles.buttonContainer}>
        <TouchableOpacity style={styles.button}>
          <ThemedText style={styles.buttonText} onPress={() => router.push('/UberShare')}>
            Share Uber 🚕</ThemedText>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.button, { backgroundColor: '#1dd1a1' }]}
          onPress={() => router.push('/FindDrivers')}>
          <ThemedText style={styles.buttonText}>Find Drivers🤵</ThemedText>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.button, { backgroundColor: '#54a0ff' }]}
          onPress={() => router.push('/FindRiders')}>
          <ThemedText style={styles.buttonText}>Find Riders🧍‍♂️🧍‍♀️</ThemedText>
        </TouchableOpacity>
      </ThemedView>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  reactLogo: {
    height: 250,
    width: '100%',
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
  buttonContainer: {
    marginTop: 24,
    gap: 16,
  },
  button: {
    backgroundColor: '#f284ba',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});