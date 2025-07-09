import React, { useState } from 'react';
import { 
  View, 
  StyleSheet, 
  Alert, 
  TouchableOpacity, 
  Image 
} from 'react-native';
import { 
  Avatar, 
  IconButton, 
  Button, 
  Portal, 
  Modal, 
  Text 
} from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface ProfilePictureProps {
  profilePicture?: string;
  name?: string;
  email: string;
  size?: number;
  editable?: boolean;
  onImageUpdate?: (newImageData: string) => void;
}

export default function ProfilePicture({
  profilePicture,
  name,
  email,
  size = 80,
  editable = false,
  onImageUpdate
}: ProfilePictureProps) {
  const [uploading, setUploading] = useState(false);
  const [showImageOptions, setShowImageOptions] = useState(false);

  const requestPermissions = async () => {
    const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();
    const { status: mediaLibraryStatus } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (cameraStatus !== 'granted' || mediaLibraryStatus !== 'granted') {
      Alert.alert(
        'Permissions Required',
        'Camera and photo library permissions are required to upload a profile picture.',
        [{ text: 'OK' }]
      );
      return false;
    }
    return true;
  };

  const processImage = async (uri: string) => {
    try {
      // Resize and compress the image
      const manipulatedImage = await ImageManipulator.manipulateAsync(
        uri,
        [
          { resize: { width: 300, height: 300 } } // Resize to 300x300
        ],
        {
          compress: 0.7, // Compress to 70% quality
          format: ImageManipulator.SaveFormat.JPEG,
          base64: true
        }
      );

      if (!manipulatedImage.base64) {
        throw new Error('Failed to process image');
      }

      // Create data URL
      const dataUrl = `data:image/jpeg;base64,${manipulatedImage.base64}`;
      
      return dataUrl;
    } catch (error) {
      console.error('Error processing image:', error);
      throw error;
    }
  };

  const uploadImage = async (imageData: string) => {
    try {
      setUploading(true);
      
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/profile/picture`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_data: imageData
        })
      });

      if (response.ok) {
        const updatedProfile = await response.json();
        onImageUpdate?.(updatedProfile.profile_picture);
        Alert.alert('Success', 'Profile picture updated successfully!');
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to update profile picture');
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      Alert.alert('Error', 'Unable to upload image. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleImagePicker = async (useCamera: boolean) => {
    setShowImageOptions(false);
    
    const hasPermissions = await requestPermissions();
    if (!hasPermissions) return;

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        const imageUri = result.assets[0].uri;
        const processedImage = await processImage(imageUri);
        await uploadImage(processedImage);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to select image. Please try again.');
    }
  };

  const handleCameraPicker = async () => {
    setShowImageOptions(false);
    
    const hasPermissions = await requestPermissions();
    if (!hasPermissions) return;

    try {
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        const imageUri = result.assets[0].uri;
        const processedImage = await processImage(imageUri);
        await uploadImage(processedImage);
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo. Please try again.');
    }
  };

  const getInitial = () => {
    if (name) return name.charAt(0).toUpperCase();
    return email.charAt(0).toUpperCase();
  };

  return (
    <View style={styles.container}>
      <View style={styles.avatarContainer}>
        {profilePicture ? (
          <TouchableOpacity 
            disabled={!editable || uploading}
            onPress={() => editable && setShowImageOptions(true)}
          >
            <Image
              source={{ uri: profilePicture }}
              style={[styles.profileImage, { width: size, height: size }]}
            />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity 
            disabled={!editable || uploading}
            onPress={() => editable && setShowImageOptions(true)}
          >
            <Avatar.Text
              size={size}
              label={getInitial()}
              style={styles.avatar}
            />
          </TouchableOpacity>
        )}
        
        {editable && (
          <IconButton
            icon="camera"
            size={20}
            iconColor="white"
            style={styles.cameraIcon}
            onPress={() => setShowImageOptions(true)}
            disabled={uploading}
          />
        )}
      </View>

      {/* Image Options Modal */}
      <Portal>
        <Modal
          visible={showImageOptions}
          onDismiss={() => setShowImageOptions(false)}
          contentContainerStyle={styles.modalContainer}
        >
          <Text style={styles.modalTitle}>Select Photo</Text>
          <View style={styles.optionContainer}>
            <Button
              mode="outlined"
              onPress={handleCameraPicker}
              style={styles.optionButton}
              icon="camera"
            >
              Take Photo
            </Button>
            <Button
              mode="outlined"
              onPress={() => handleImagePicker(false)}
              style={styles.optionButton}
              icon="image"
            >
              Choose from Gallery
            </Button>
          </View>
          <Button
            mode="text"
            onPress={() => setShowImageOptions(false)}
            style={styles.cancelButton}
          >
            Cancel
          </Button>
        </Modal>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  avatarContainer: {
    position: 'relative',
  },
  profileImage: {
    borderRadius: 40,
    borderWidth: 2,
    borderColor: '#ddd',
  },
  avatar: {
    backgroundColor: '#2196F3',
  },
  cameraIcon: {
    position: 'absolute',
    bottom: -5,
    right: -5,
    backgroundColor: '#2196F3',
    borderRadius: 15,
    width: 30,
    height: 30,
  },
  modalContainer: {
    backgroundColor: 'white',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
  },
  optionContainer: {
    gap: 12,
    marginBottom: 20,
  },
  optionButton: {
    borderColor: '#2196F3',
  },
  cancelButton: {
    alignSelf: 'center',
  },
});