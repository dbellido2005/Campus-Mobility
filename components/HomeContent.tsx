import React, { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ProfileScreen from '@/components/ProfileScreen';
import LoginScreen from '@/components/auth/LoginScreen';
import SignUpScreen from '@/components/auth/SignUpScreen';
import EmailVerificationScreen from '@/components/auth/EmailVerificationScreen';
import ForgotPasswordScreen from '@/components/auth/ForgotPasswordScreen';
import Loading from '@/app/Loading';
import { College } from '@/utils/collegeUtils';

type AuthState = 'loading' | 'login' | 'signup' | 'verification' | 'forgot-password' | 'authenticated';

interface VerificationData {
  email: string;
  college: College;
}

export default function HomeContent() {
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

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('user');
      setAuthState('login');
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  const handleLoginSuccess = async (userData: any) => {
    try {
      if (userData.access_token || userData.token) {
        const token = userData.access_token || userData.token;
        await AsyncStorage.setItem('userToken', token);
        await AsyncStorage.setItem('user', JSON.stringify(userData.user || userData));
        setAuthState('authenticated');
      } else {
        console.error('No token received from server');
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
      if (userData.access_token || userData.token) {
        const token = userData.access_token || userData.token;
        await AsyncStorage.setItem('userToken', token);
        await AsyncStorage.setItem('user', JSON.stringify(userData.user || userData));
        setAuthState('authenticated');
      } else {
        console.error('No token received from server');
      }
    } catch (error) {
      console.error('Error storing user data:', error);
    }
  };

  if (authState === 'loading') {
    return <Loading />;
  }

  if (authState === 'authenticated') {
    return <ProfileScreen onLogout={handleLogout} />;
  }

  return (
    <>
      {authState === 'login' && (
        <LoginScreen
          onLoginSuccess={handleLoginSuccess}
          onSwitchToSignUp={() => setAuthState('signup')}
          onForgotPassword={() => setAuthState('forgot-password')}
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
      
      {authState === 'forgot-password' && (
        <ForgotPasswordScreen
          onBackToLogin={() => setAuthState('login')}
          onResetSuccess={() => setAuthState('login')}
        />
      )}
    </>
  );
}