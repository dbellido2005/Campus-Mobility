import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Text,
  RefreshControl,
} from 'react-native';
import { TextInput, Button, Card, Chip, IconButton } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface Message {
  message_id: string;
  sender_email: string;
  sender_name?: string;
  content: string;
  timestamp: string;
  message_type: string;
}

interface GroupChatResponse {
  ride_id: string;
  messages: Message[];
  participant_count: number;
}

interface Question {
  question_id: string;
  asker_email: string;
  asker_name?: string;
  question: string;
  timestamp: string;
  response_count: number;
}

interface GroupChatScreenProps {
  rideId: string;
  onBack: () => void;
}

export default function GroupChatScreen({ rideId, onBack }: GroupChatScreenProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentUserEmail, setCurrentUserEmail] = useState<string | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    getCurrentUserEmail();
    loadChatData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadChatData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getCurrentUserEmail = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        const user = JSON.parse(userData);
        setCurrentUserEmail(user.email);
      }
    } catch (error) {
      console.error('Error getting user email:', error);
    }
  };

  const loadChatData = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      // Load messages and questions in parallel
      const [messagesResponse, questionsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/ride/${rideId}/messages`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE_URL}/ride/${rideId}/questions`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (messagesResponse.ok) {
        const chatData: GroupChatResponse = await messagesResponse.json();
        setMessages(chatData.messages);
      }

      if (questionsResponse.ok) {
        const questionsData: Question[] = await questionsResponse.json();
        setQuestions(questionsData);
      }

    } catch (error) {
      console.error('Error loading chat data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ride/${rideId}/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ride_id: rideId,
          content: newMessage.trim()
        })
      });

      if (response.ok) {
        setNewMessage('');
        loadChatData(); // Refresh messages
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Error', 'Unable to send message');
    }
  };

  const respondToQuestion = async (questionId: string) => {
    Alert.prompt(
      'Respond to Question',
      'Enter your private response:',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Send',
          onPress: async (response) => {
            if (!response?.trim()) return;

            try {
              const token = await AsyncStorage.getItem('userToken');
              if (!token) {
                Alert.alert('Error', 'Please login again');
                return;
              }

              const apiResponse = await fetch(`${API_BASE_URL}/question/${questionId}/respond`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  question_id: questionId,
                  response: response.trim()
                })
              });

              if (apiResponse.ok) {
                Alert.alert('Success', 'Response sent privately to the question asker');
                loadChatData(); // Refresh to update response counts
              } else {
                const error = await apiResponse.json();
                Alert.alert('Error', error.detail || 'Failed to send response');
              }
            } catch (error) {
              console.error('Error sending response:', error);
              Alert.alert('Error', 'Unable to send response');
            }
          }
        }
      ],
      'plain-text'
    );
  };

  const formatTime = (timestamp: string) => {
    // Create date from timestamp (should automatically handle timezone conversion)
    const date = new Date(timestamp);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid timestamp:', timestamp);
      return 'Invalid time';
    }
    
    // Format using device's local timezone
    return date.toLocaleTimeString(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid timestamp for date:', timestamp);
      return 'Invalid date';
    }
    
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const renderMessage = (message: Message, index: number) => {
    const isOwnMessage = message.sender_email === currentUserEmail;
    const showDate = index === 0 || 
      formatDate(message.timestamp) !== formatDate(messages[index - 1]?.timestamp);

    return (
      <View key={message.message_id}>
        {showDate && (
          <Text style={styles.dateHeader}>
            {formatDate(message.timestamp)}
          </Text>
        )}
        
        {message.message_type === 'question' ? (
          <Card style={styles.questionCard}>
            <Card.Content>
              <View style={styles.questionHeader}>
                <Chip icon="help-circle" style={styles.questionChip}>
                  Question
                </Chip>
                <Text style={styles.questionTime}>
                  {formatTime(message.timestamp)}
                </Text>
              </View>
              <Text style={styles.questionAuthor}>
                {message.sender_name || message.sender_email}
              </Text>
              <Text style={styles.questionContent}>
                {message.content.replace('QUESTION: ', '')}
              </Text>
              <Button
                mode="outlined"
                onPress={() => message.question_id && respondToQuestion(message.question_id)}
                style={styles.respondButton}
                icon="reply"
              >
                Respond Privately
              </Button>
            </Card.Content>
          </Card>
        ) : (
          <View style={[
            styles.messageContainer,
            isOwnMessage ? styles.ownMessage : styles.otherMessage
          ]}>
            {!isOwnMessage && (
              <Text style={styles.senderName}>
                {message.sender_name || message.sender_email}
              </Text>
            )}
            <Text style={styles.messageContent}>
              {message.content}
            </Text>
            <Text style={styles.messageTime}>
              {formatTime(message.timestamp)}
            </Text>
          </View>
        )}
      </View>
    );
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadChatData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading chat...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.header}>
        <IconButton icon="arrow-left" onPress={onBack} />
        <Text style={styles.headerTitle}>Ride Chat</Text>
        <IconButton icon="refresh" onPress={loadChatData} />
      </View>

      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        onContentSizeChange={() => {
          scrollViewRef.current?.scrollToEnd({ animated: true });
        }}
      >
        {messages.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No messages yet</Text>
            <Text style={styles.emptySubtext}>
              Start the conversation!
            </Text>
          </View>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TextInput
          mode="outlined"
          placeholder="Type a message..."
          value={newMessage}
          onChangeText={setNewMessage}
          style={styles.messageInput}
          multiline
          maxLength={500}
          right={
            <TextInput.Icon
              icon="send"
              onPress={sendMessage}
              disabled={!newMessage.trim()}
            />
          }
        />
      </View>
    </KeyboardAvoidingView>
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
    marginRight: 48, // Compensate for right icon
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 100,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
  },
  dateHeader: {
    textAlign: 'center',
    fontSize: 12,
    color: '#666',
    marginVertical: 16,
    backgroundColor: '#e0e0e0',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'center',
  },
  messageContainer: {
    marginVertical: 4,
    padding: 12,
    borderRadius: 16,
    maxWidth: '80%',
  },
  ownMessage: {
    backgroundColor: '#2196F3',
    alignSelf: 'flex-end',
  },
  otherMessage: {
    backgroundColor: '#fff',
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  senderName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 4,
  },
  messageContent: {
    fontSize: 14,
    color: '#333',
  },
  messageTime: {
    fontSize: 10,
    color: '#999',
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  questionCard: {
    marginVertical: 8,
    backgroundColor: '#fff3e0',
    borderLeftWidth: 4,
    borderLeftColor: '#ff9800',
  },
  questionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  questionChip: {
    backgroundColor: '#ffcc80',
  },
  questionTime: {
    fontSize: 10,
    color: '#666',
  },
  questionAuthor: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 4,
  },
  questionContent: {
    fontSize: 14,
    color: '#333',
    marginBottom: 12,
  },
  respondButton: {
    alignSelf: 'flex-start',
  },
  inputContainer: {
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  messageInput: {
    backgroundColor: '#fff',
  },
});