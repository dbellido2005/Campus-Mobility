import React, { useState, useEffect } from "react";
import { View, TextInput, Button, Text, StyleSheet, Alert, TouchableOpacity, ScrollView, Keyboard } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { NativeStackScreenProps } from '@react-navigation/native-stack';


type RootStackParamList = {
    Login: undefined;
    Home: undefined; // or whatever your home screen is called
  };

type Props = NativeStackScreenProps<RootStackParamList, 'Login'>;


const LoginScreen = ({ navigation }: Props) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const handleLogin = async () => {
    try {
      const response = await fetch("http://172.28.119.64:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        await AsyncStorage.setItem("user", JSON.stringify(data));
        navigation.replace("Home");  // or your main screen
      } else {
        Alert.alert("Login failed", "Invalid email or password");
      }
    } catch (err) {
      Alert.alert("Error", "Unable to connect to server");
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      Alert.alert("Error", "Please enter your email address");
      return;
    }

    try {
      const response = await fetch("http://172.28.119.64:8000/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        Alert.alert("Success", "Password reset code sent to your email");
        setShowForgotPassword(true);
      } else {
        const errorData = await response.json();
        Alert.alert("Error", errorData.detail || "Failed to send reset code");
      }
    } catch (err) {
      Alert.alert("Error", "Unable to connect to server");
    }
  };

  const handleResetPassword = async () => {
    if (!resetCode || !newPassword) {
      Alert.alert("Error", "Please enter the reset code and new password");
      return;
    }

    try {
      const response = await fetch("http://172.28.119.64:8000/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, reset_code: resetCode, new_password: newPassword }),
      });

      if (response.ok) {
        Alert.alert("Success", "Password reset successfully");
        setShowForgotPassword(false);
        setResetCode("");
        setNewPassword("");
      } else {
        const errorData = await response.json();
        Alert.alert("Error", errorData.detail || "Failed to reset password");
      }
    } catch (err) {
      Alert.alert("Error", "Unable to connect to server");
    }
  };

  useEffect(() => {
    const checkLogin = async () => {
      const storedUser = await AsyncStorage.getItem("user");
      if (storedUser) {
        navigation.replace("Home");
      }
    };
    checkLogin();
  }, []);

  return (
    <ScrollView 
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
      onScrollBeginDrag={() => Keyboard.dismiss()}
    >
    <View style={styles.innerContainer}>
      <TextInput
        placeholder="Email"
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
      />
      
      {!showForgotPassword ? (
        <>
          <TextInput
            placeholder="Password"
            style={styles.input}
            value={password}
            secureTextEntry
            onChangeText={setPassword}
          />
          <Button title="Log In" onPress={handleLogin} />
          <TouchableOpacity onPress={handleForgotPassword} style={styles.forgotButton}>
            <Text style={styles.forgotText}>Forgot Password?</Text>
          </TouchableOpacity>
        </>
      ) : (
        <>
          <TextInput
            placeholder="Reset Code (6 digits)"
            style={styles.input}
            value={resetCode}
            onChangeText={setResetCode}
            keyboardType="numeric"
          />
          <TextInput
            placeholder="New Password"
            style={styles.input}
            value={newPassword}
            secureTextEntry
            onChangeText={setNewPassword}
          />
          <Button title="Reset Password" onPress={handleResetPassword} />
          <TouchableOpacity onPress={() => setShowForgotPassword(false)} style={styles.forgotButton}>
            <Text style={styles.forgotText}>Back to Login</Text>
          </TouchableOpacity>
        </>
      )}
    </View>
    </ScrollView>
  );
};

export default LoginScreen;

const styles = StyleSheet.create({
  container: { flexGrow: 1, justifyContent: "center", padding: 20 },
  innerContainer: { flex: 1, justifyContent: "center" },
  input: { borderWidth: 1, marginBottom: 10, padding: 10, borderRadius: 5 },
  forgotButton: { marginTop: 10, alignItems: "center" },
  forgotText: { color: "#007AFF", textDecorationLine: "underline" },
});
