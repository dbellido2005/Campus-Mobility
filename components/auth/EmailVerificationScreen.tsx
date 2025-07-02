import React, { useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { TextInput, Button, Text, Card } from 'react-native-paper';
import { College } from '../../utils/collegeUtils';

interface EmailVerificationScreenProps {
  email: string;
  college: College;
  onVerificationSuccess: (userData: any) => void;
  onBack: () => void;
}

export default function EmailVerificationScreen({ 
  email, 
  college, 
  onVerificationSuccess, 
  onBack 
}: EmailVerificationScreenProps) {
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  const handleVerifyEmail = async () => {
    if (!verificationCode.trim()) {
      Alert.alert('Error', 'Please enter the verification code');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://172.28.119.64:8000/verify-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: email.toLowerCase(),
          code: verificationCode.trim()
        }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert(
          'Email Verified!',
          `Welcome to Campus Mobility! Your ${college.name} account has been created.`,
          [{ text: 'Continue', onPress: () => onVerificationSuccess(data.user) }]
        );
      } else {
        Alert.alert('Verification Failed', data.message || 'Invalid verification code');
      }
    } catch (error) {
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setResendLoading(true);

    try {
      const response = await fetch('http://172.28.119.64:8000/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.toLowerCase() }),
      });

      if (response.ok) {
        Alert.alert('Success', 'Verification code sent to your email');
      } else {
        Alert.alert('Error', 'Failed to resend verification code');
      }
    } catch (error) {
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="headlineMedium" style={styles.title}>
            Verify Your Email
          </Text>
          
          <Text variant="bodyMedium" style={styles.subtitle}>
            We sent a verification code to
          </Text>
          <Text variant="bodyLarge" style={styles.email}>
            {email}
          </Text>
          
          <Text variant="bodyMedium" style={styles.collegeInfo}>
            Campus: {college.name}
          </Text>

          <TextInput
            label="Verification Code"
            value={verificationCode}
            onChangeText={setVerificationCode}
            autoCapitalize="characters"
            style={styles.input}
            mode="outlined"
            placeholder="Enter 6-digit code"
          />

          <Button
            mode="contained"
            onPress={handleVerifyEmail}
            loading={loading}
            disabled={loading}
            style={styles.button}
          >
            Verify Email
          </Button>

          <Button
            mode="text"
            onPress={handleResendCode}
            loading={resendLoading}
            disabled={resendLoading}
            style={styles.resendButton}
          >
            Resend Code
          </Button>

          <Button
            mode="outlined"
            onPress={onBack}
            style={styles.backButton}
          >
            Back to Sign Up
          </Button>
        </Card.Content>
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    padding: 16,
  },
  title: {
    textAlign: 'center',
    marginBottom: 16,
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: 4,
  },
  email: {
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: 8,
  },
  collegeInfo: {
    textAlign: 'center',
    marginBottom: 24,
    color: '#666',
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginBottom: 12,
  },
  resendButton: {
    marginBottom: 24,
  },
  backButton: {
    marginTop: 8,
  },
});