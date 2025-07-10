import React, { useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { TextInput, Button, Text, Card } from 'react-native-paper';

interface ForgotPasswordScreenProps {
  onBackToLogin: () => void;
  onResetSuccess: () => void;
}

export default function ForgotPasswordScreen({ onBackToLogin, onResetSuccess }: ForgotPasswordScreenProps) {
  const [email, setEmail] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'email' | 'reset'>('email');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSendResetCode = async () => {
    if (!email.trim()) {
      Alert.alert('Error', 'Please enter your email address');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://172.28.119.64:8000/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.toLowerCase().trim() }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert(
          'Reset Code Sent',
          'Please check your email for the password reset code.',
          [{ text: 'OK', onPress: () => setStep('reset') }]
        );
      } else {
        Alert.alert('Error', data.detail || data.message || 'Failed to send reset code');
      }
    } catch (error) {
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!resetCode.trim()) {
      Alert.alert('Error', 'Please enter the reset code');
      return;
    }

    if (!newPassword.trim() || !confirmPassword.trim()) {
      Alert.alert('Error', 'Please enter and confirm your new password');
      return;
    }

    if (newPassword !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters long');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://172.28.119.64:8000/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.toLowerCase().trim(),
          reset_code: resetCode.trim(),
          new_password: newPassword
        }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert(
          'Password Reset Successful',
          'Your password has been reset successfully. You can now log in with your new password.',
          [{ text: 'OK', onPress: onResetSuccess }]
        );
      } else {
        Alert.alert('Error', data.detail || data.message || 'Failed to reset password');
      }
    } catch (error) {
      Alert.alert('Error', 'Unable to connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="headlineMedium" style={styles.title}>
            {step === 'email' ? 'Forgot Password?' : 'Reset Password'}
          </Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            {step === 'email' 
              ? 'Enter your email address and we\'ll send you a reset code'
              : 'Enter the reset code and your new password'
            }
          </Text>

          {step === 'email' ? (
            <>
              <TextInput
                label="Email"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
                style={styles.input}
                mode="outlined"
              />

              <Button
                mode="contained"
                onPress={handleSendResetCode}
                loading={loading}
                disabled={loading}
                style={styles.button}
              >
                Send Reset Code
              </Button>
            </>
          ) : (
            <>
              <TextInput
                label="Reset Code"
                value={resetCode}
                onChangeText={setResetCode}
                keyboardType="numeric"
                style={styles.input}
                mode="outlined"
                placeholder="Enter 6-digit code"
              />

              <TextInput
                label="New Password"
                value={newPassword}
                onChangeText={setNewPassword}
                secureTextEntry={!showNewPassword}
                style={styles.input}
                mode="outlined"
                right={
                  <TextInput.Icon
                    icon={showNewPassword ? "eye-off" : "eye"}
                    onPress={() => setShowNewPassword(!showNewPassword)}
                  />
                }
              />

              <TextInput
                label="Confirm New Password"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry={!showConfirmPassword}
                style={styles.input}
                mode="outlined"
                right={
                  <TextInput.Icon
                    icon={showConfirmPassword ? "eye-off" : "eye"}
                    onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                  />
                }
              />

              <Button
                mode="contained"
                onPress={handleResetPassword}
                loading={loading}
                disabled={loading}
                style={styles.button}
              >
                Reset Password
              </Button>

              <Button
                mode="text"
                onPress={() => setStep('email')}
                style={styles.backButton}
              >
                Back to Email Entry
              </Button>
            </>
          )}

          <Button
            mode="text"
            onPress={onBackToLogin}
            style={styles.switchButton}
          >
            Back to Login
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
    marginBottom: 8,
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: 24,
    opacity: 0.7,
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 8,
    marginBottom: 16,
  },
  backButton: {
    marginTop: 4,
    marginBottom: 8,
  },
  switchButton: {
    marginTop: 8,
  },
});