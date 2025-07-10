import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, Text } from 'react-native';
import { Button, Card, IconButton } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

import GroupChatScreen from './GroupChatScreen';
import AskQuestionScreen from './AskQuestionScreen';
import MyQuestionsScreen from './MyQuestionsScreen';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface ChatInfo {
  is_member: boolean;
  message_count: number;
  question_count: number;
  can_send_messages: boolean;
  can_ask_questions: boolean;
}

interface MessagingScreenProps {
  rideId: string;
  onBack: () => void;
}

type ScreenState = 'main' | 'group-chat' | 'ask-question' | 'my-questions';

export default function MessagingScreen({ rideId, onBack }: MessagingScreenProps) {
  const [chatInfo, setChatInfo] = useState<ChatInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentScreen, setCurrentScreen] = useState<ScreenState>('main');
  const [hasAutoNavigated, setHasAutoNavigated] = useState(false);

  useEffect(() => {
    loadChatInfo();
  }, []);

  const loadChatInfo = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride/${rideId}/chat-info`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const info: ChatInfo = await response.json();
        setChatInfo(info);
        
        // If user is a member and there are messages, go directly to group chat (only on initial load)
        if (info.is_member && info.message_count > 0 && !hasAutoNavigated) {
          setCurrentScreen('group-chat');
          setHasAutoNavigated(true);
        }
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to load chat info');
      }
    } catch (error) {
      console.error('Error loading chat info:', error);
      Alert.alert('Error', 'Unable to load chat info');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (currentScreen === 'main') {
      onBack();
    } else {
      setCurrentScreen('main');
      // Don't call loadChatInfo here to prevent auto-navigation loop
    }
  };

  const handleQuestionSent = () => {
    setCurrentScreen('my-questions');
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading...</Text>
      </View>
    );
  }

  if (!chatInfo) {
    return (
      <View style={styles.errorContainer}>
        <Text>Unable to load chat information</Text>
        <Button onPress={onBack}>Go Back</Button>
      </View>
    );
  }

  // Show specific screens
  if (currentScreen === 'group-chat' && chatInfo.is_member) {
    return (
      <GroupChatScreen
        rideId={rideId}
        onBack={handleBack}
      />
    );
  }

  if (currentScreen === 'ask-question' && !chatInfo.is_member) {
    return (
      <AskQuestionScreen
        rideId={rideId}
        onBack={handleBack}
        onQuestionSent={handleQuestionSent}
      />
    );
  }

  if (currentScreen === 'my-questions') {
    return (
      <MyQuestionsScreen
        onBack={handleBack}
      />
    );
  }

  // Main screen - show options based on membership
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <IconButton icon="arrow-left" onPress={handleBack} />
        <Text style={styles.headerTitle}>Ride Communication</Text>
        <View style={{ width: 48 }} />
      </View>

      <View style={styles.content}>
        {chatInfo.is_member ? (
          // Member interface
          <View>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>👥 Group Chat</Text>
                <Text style={styles.infoText}>
                  You are a member of this ride. You can chat with other ride members.
                </Text>
                <Text style={styles.statsText}>
                  {chatInfo.message_count} message{chatInfo.message_count !== 1 ? 's' : ''} • {chatInfo.question_count} question{chatInfo.question_count !== 1 ? 's' : ''}
                </Text>
              </Card.Content>
            </Card>

            <Button
              mode="contained"
              onPress={() => setCurrentScreen('group-chat')}
              style={styles.actionButton}
              icon="chat"
            >
              Open Group Chat
            </Button>

            {chatInfo.question_count > 0 && (
              <Text style={styles.questionsInfo}>
                💡 There {chatInfo.question_count === 1 ? 'is' : 'are'} {chatInfo.question_count} question{chatInfo.question_count !== 1 ? 's' : ''} from people interested in joining. 
                You can respond to them privately in the group chat.
              </Text>
            )}
          </View>
        ) : (
          // Non-member interface
          <View>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>❓ Ask Questions</Text>
                <Text style={styles.infoText}>
                  You can ask questions about this ride. Ride members will see your question and can respond to you privately.
                </Text>
                <Text style={styles.noteText}>
                  Note: You won't see their group conversation.
                </Text>
              </Card.Content>
            </Card>

            <Button
              mode="contained"
              onPress={() => setCurrentScreen('ask-question')}
              style={styles.actionButton}
              icon="help-circle"
            >
              Ask a Question
            </Button>

            <Button
              mode="outlined"
              onPress={() => setCurrentScreen('my-questions')}
              style={styles.secondaryButton}
              icon="message-reply"
            >
              View My Questions & Responses
            </Button>

            <Text style={styles.tipText}>
              💡 Tip: Join the ride to access the full group chat!
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
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
    padding: 16,
  },
  infoCard: {
    marginBottom: 24,
    backgroundColor: '#fff',
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 8,
  },
  noteText: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
  },
  statsText: {
    fontSize: 12,
    color: '#2196F3',
    fontWeight: 'bold',
  },
  actionButton: {
    marginBottom: 16,
    paddingVertical: 8,
  },
  secondaryButton: {
    marginBottom: 16,
    paddingVertical: 8,
  },
  questionsInfo: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#fff3e0',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ff9800',
    lineHeight: 18,
  },
  tipText: {
    fontSize: 12,
    color: '#4caf50',
    backgroundColor: '#f1f8e9',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#4caf50',
    textAlign: 'center',
    marginTop: 16,
  },
});