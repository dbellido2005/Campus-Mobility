import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  Text,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { TextInput, Button, Card, IconButton } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface AskQuestionScreenProps {
  rideId: string;
  onBack: () => void;
  onQuestionSent: () => void;
}

export default function AskQuestionScreen({ rideId, onBack, onQuestionSent }: AskQuestionScreenProps) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const sendQuestion = async () => {
    if (!question.trim()) {
      Alert.alert('Error', 'Please enter your question');
      return;
    }

    setLoading(true);

    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride/${rideId}/question`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ride_id: rideId,
          question: question.trim()
        })
      });

      if (response.ok) {
        Alert.alert(
          'Question Sent!',
          'Your question has been sent to the ride members. They can respond to you privately.',
          [{ text: 'OK', onPress: onQuestionSent }]
        );
        setQuestion('');
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to send question');
      }
    } catch (error) {
      console.error('Error sending question:', error);
      Alert.alert('Error', 'Unable to send question');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.header}>
        <IconButton icon="arrow-left" onPress={onBack} />
        <Text style={styles.headerTitle}>Ask a Question</Text>
        <View style={{ width: 48 }} />
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
        <Card style={styles.infoCard}>
          <Card.Content>
            <Text style={styles.infoTitle}>💬 How it works</Text>
            <Text style={styles.infoText}>
              • Ask questions about the ride (time changes, drop-off locations, etc.)
            </Text>
            <Text style={styles.infoText}>
              • Ride members will see your question
            </Text>
            <Text style={styles.infoText}>
              • They can respond to you privately
            </Text>
            <Text style={styles.infoText}>
              • You won't see their group conversation
            </Text>
          </Card.Content>
        </Card>

        <Card style={styles.questionCard}>
          <Card.Content>
            <Text style={styles.questionLabel}>Your Question</Text>
            <TextInput
              mode="outlined"
              placeholder="e.g., Could we leave at 10am instead of 11am? Or could you drop me off at the library instead?"
              value={question}
              onChangeText={setQuestion}
              multiline
              numberOfLines={4}
              maxLength={300}
              style={styles.questionInput}
            />
            <Text style={styles.characterCount}>
              {question.length}/300 characters
            </Text>
          </Card.Content>
        </Card>

        <Text style={styles.exampleTitle}>💡 Good question examples:</Text>
        <View style={styles.examplesContainer}>
          <Text style={styles.exampleText}>
            "Could we leave 15 minutes earlier?"
          </Text>
          <Text style={styles.exampleText}>
            "Would it be possible to drop me off at the Student Union instead?"
          </Text>
          <Text style={styles.exampleText}>
            "Do you mind if I bring a small suitcase?"
          </Text>
          <Text style={styles.exampleText}>
            "Is there room for one more person? My friend needs a ride too."
          </Text>
        </View>
      </ScrollView>

      <View style={styles.buttonContainer}>
        <Button
          mode="contained"
          onPress={sendQuestion}
          loading={loading}
          disabled={loading || !question.trim()}
          style={styles.sendButton}
          icon="send"
        >
          Send Question
        </Button>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingTop: 50,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
  },
  infoCard: {
    marginBottom: 16,
    backgroundColor: '#e3f2fd',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1976d2',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#1565c0',
    marginBottom: 4,
    lineHeight: 20,
  },
  questionCard: {
    marginBottom: 16,
  },
  questionLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333',
  },
  questionInput: {
    marginBottom: 8,
    backgroundColor: '#fff',
  },
  characterCount: {
    fontSize: 12,
    color: '#666',
    textAlign: 'right',
  },
  exampleTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333',
  },
  examplesContainer: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#4caf50',
  },
  exampleText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  buttonContainer: {
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  sendButton: {
    paddingVertical: 8,
  },
});