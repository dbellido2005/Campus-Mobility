import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import HomeContent from '@/components/HomeContent';
import LoginScreen from '@/components/auth/LoginScreen';
import SignUpScreen from '@/components/auth/SignUpScreen';
import EmailVerificationScreen from '@/components/auth/EmailVerificationScreen';
import Loading from '@/app/Loading';
import { College } from '@/utils/collegeUtils';

type AuthState = 'loading' | 'login' | 'signup' | 'verification' | 'authenticated';

interface VerificationData {
  email: string;
  college: College;
}

export default function HomeScreen() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [verificationData, setVerificationData] = useState<VerificationData | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const userToken = await AsyncStorage.getItem('userToken');
      const userData = await AsyncStorage.getItem('user');
      
      if (userToken && userData) {
        setAuthState('authenticated');
      } else {
        setAuthState('login');
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setAuthState('login');
    }
  };

  const handleLoginSuccess = async (userData: any) => {
    try {
      // Check if token exists before storing
      if (userData.access_token || userData.token) {
        const token = userData.access_token || userData.token;
        await AsyncStorage.setItem('userToken', token);
        await AsyncStorage.setItem('user', JSON.stringify(userData.user || userData));
        setAuthState('authenticated');
      } else {
        console.error('No token received from server');
        Alert.alert('Error', 'Authentication failed - no token received');
      }
    } catch (error) {
      console.error('Error storing user data:', error);
    }
  };

  const handleSignUpSuccess = (email: string, college: College) => {
    setVerificationData({ email, college });
    setAuthState('verification');
  };

  const handleVerificationSuccess = async (userData: any) => {
    try {
      // Check if token exists before storing
      if (userData.access_token || userData.token) {
        const token = userData.access_token || userData.token;
        await AsyncStorage.setItem('userToken', token);
        await AsyncStorage.setItem('user', JSON.stringify(userData.user || userData));
        setAuthState('authenticated');
      } else {
        console.error('No token received from server');
        Alert.alert('Error', 'Authentication failed - no token received');
      }
    } catch (error) {
      console.error('Error storing user data:', error);
    }
  };

  if (authState === 'loading') {
    return <Loading />;
  }

  if (authState === 'authenticated') {
    return <HomeContent />;
  }

  return (
    <View style={styles.container}>
      {authState === 'login' && (
        <LoginScreen
          onLoginSuccess={handleLoginSuccess}
          onSwitchToSignUp={() => setAuthState('signup')}
        />
      )}
      
      {authState === 'signup' && (
        <SignUpScreen
          onSignUpSuccess={handleSignUpSuccess}
          onSwitchToLogin={() => setAuthState('login')}
        />
      )}
      
      {authState === 'verification' && verificationData && (
        <EmailVerificationScreen
          email={verificationData.email}
          college={verificationData.college}
          onVerificationSuccess={handleVerificationSuccess}
          onBack={() => setAuthState('signup')}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
