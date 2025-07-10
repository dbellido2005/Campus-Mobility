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
  Modal,
  Image,
  Keyboard,
  TouchableWithoutFeedback,
  Dimensions,
} from 'react-native';
// import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { TextInput, Button, Card, Chip, IconButton } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface Message {
  message_id: string;
  sender_email: string;
  sender_name?: string;
  sender_profile_picture?: string;  // Profile picture URL or base64
  content: string;
  timestamp: string;
  message_type: string;
  question_id?: string;  // For question-type messages
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
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  
  // Response modal state
  const [responseModalVisible, setResponseModalVisible] = useState(false);
  const [responseText, setResponseText] = useState('');
  const [currentQuestionId, setCurrentQuestionId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    getCurrentUserEmail();
    loadChatData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadChatData, 30000);
    
    // Keyboard event listeners for better chat experience
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', (event) => {
      setKeyboardHeight(event.endCoordinates.height);
      // Scroll to bottom when keyboard shows
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    });
    
    const keyboardDidHideListener = Keyboard.addListener('keyboardDidHide', () => {
      setKeyboardHeight(0);
    });
    
    return () => {
      clearInterval(interval);
      keyboardDidShowListener?.remove();
      keyboardDidHideListener?.remove();
    };
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
    if (!newMessage.trim() || sending) return;

    try {
      setSending(true);
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        setSending(false);
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
    } finally {
      setSending(false);
    }
  };

  const openResponseModal = (questionId: string) => {
    setCurrentQuestionId(questionId);
    setResponseText('');
    setResponseModalVisible(true);
  };

  const closeResponseModal = () => {
    setResponseModalVisible(false);
    setCurrentQuestionId(null);
    setResponseText('');
  };

  const sendPrivateResponse = async () => {
    if (!responseText.trim() || !currentQuestionId) return;

    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const apiResponse = await fetch(`${API_BASE_URL}/question/${currentQuestionId}/respond`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question_id: currentQuestionId,
          response: responseText.trim()
        })
      });

      if (apiResponse.ok) {
        Alert.alert('Success', 'Response sent privately to the question asker');
        closeResponseModal();
        loadChatData(); // Refresh to update response counts
      } else {
        const error = await apiResponse.json();
        Alert.alert('Error', error.detail || 'Failed to send response');
      }
    } catch (error) {
      console.error('Error sending response:', error);
      Alert.alert('Error', 'Unable to send response');
    }
  };

  const formatTime = (timestamp: string) => {
    // Ensure proper timestamp parsing with timezone handling
    let date: Date;
    
    // Handle different timestamp formats
    if (timestamp.endsWith('Z') || timestamp.includes('+') || timestamp.includes('-')) {
      // Already has timezone info
      date = new Date(timestamp);
    } else {
      // Assume UTC if no timezone specified
      date = new Date(timestamp + (timestamp.includes('T') ? 'Z' : 'T00:00:00Z'));
    }
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid timestamp:', timestamp);
      return 'Invalid time';
    }
    
    // Format using device's local timezone - this automatically converts from UTC
    return date.toLocaleTimeString([], {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
  };

  const renderProfilePicture = (message: Message) => {
    if (message.sender_profile_picture) {
      return (
        <Image
          source={{ uri: message.sender_profile_picture }}
          style={styles.profilePicture}
        />
      );
    } else {
      // Default avatar with initials
      const initials = message.sender_name 
        ? message.sender_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : message.sender_email[0].toUpperCase();
      
      return (
        <View style={styles.defaultAvatar}>
          <Text style={styles.avatarText}>{initials}</Text>
        </View>
      );
    }
  };

  const formatDate = (timestamp: string) => {
    // Ensure proper timestamp parsing with timezone handling
    let date: Date;
    
    // Handle different timestamp formats
    if (timestamp.endsWith('Z') || timestamp.includes('+') || timestamp.includes('-')) {
      // Already has timezone info
      date = new Date(timestamp);
    } else {
      // Assume UTC if no timezone specified
      date = new Date(timestamp + (timestamp.includes('T') ? 'Z' : 'T00:00:00Z'));
    }
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid timestamp for date:', timestamp);
      return 'Invalid date';
    }
    
    // Get current date in local timezone
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Convert message date to local date for comparison
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    if (messageDate.getTime() === today.getTime()) {
      return 'Today';
    } else if (messageDate.getTime() === yesterday.getTime()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString([], {
        month: 'short',
        day: 'numeric',
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
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
                onPress={() => message.question_id && openResponseModal(message.question_id)}
                style={styles.respondButton}
                icon="reply"
              >
                Respond Privately
              </Button>
            </Card.Content>
          </Card>
        ) : message.message_type === 'response' ? (
          <Card style={styles.responseCard}>
            <Card.Content>
              <View style={styles.responseHeader}>
                <Chip icon="reply" style={styles.responseChip}>
                  Response
                </Chip>
                <Text style={styles.responseTime}>
                  {formatTime(message.timestamp)}
                </Text>
              </View>
              <Text style={styles.responseAuthor}>
                {message.sender_name || message.sender_email}
              </Text>
              <Text style={styles.responseContent}>
                {message.content.replace('RESPONSE: ', '')}
              </Text>
              <Button
                mode="outlined"
                onPress={() => message.question_id && openResponseModal(message.question_id)}
                style={styles.respondButton}
                icon="reply"
                size="small"
              >
                Add Another Response
              </Button>
            </Card.Content>
          </Card>
        ) : (
          <View style={[
            styles.messageRow,
            isOwnMessage ? styles.ownMessageRow : styles.otherMessageRow
          ]}>
            {!isOwnMessage && renderProfilePicture(message)}
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
    <View style={styles.container}>
      <View style={styles.header}>
        <IconButton icon="arrow-left" onPress={onBack} />
        <Text style={styles.headerTitle}>Ride Chat</Text>
        <IconButton icon="refresh" onPress={loadChatData} />
      </View>

      <View style={[styles.chatContainer, { paddingBottom: keyboardHeight }]}>
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={[styles.messagesContent, { paddingBottom: keyboardHeight > 0 ? 10 : 0 }]}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          onContentSizeChange={() => {
            scrollViewRef.current?.scrollToEnd({ animated: true });
          }}
          keyboardShouldPersistTaps="handled"
          onScrollBeginDrag={() => Keyboard.dismiss()}
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

        <View style={[
          styles.inputContainer,
          { 
            position: keyboardHeight > 0 ? 'absolute' : 'relative',
            bottom: keyboardHeight > 0 ? keyboardHeight : 0,
            left: 0,
            right: 0,
          }
        ]}>
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
                disabled={!newMessage.trim() || sending}
              />
            }
            onSubmitEditing={sendMessage}
          />
        </View>
      </View>

      {/* Private Response Modal */}
      <Modal
        visible={responseModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={closeResponseModal}
      >
        <TouchableWithoutFeedback onPress={() => Keyboard.dismiss()}>
          <View style={styles.modalOverlay}>
            <TouchableWithoutFeedback onPress={() => {}}>
              <KeyboardAvoidingView 
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={styles.modalContainer}
              >
                <Text style={styles.modalTitle}>Respond Privately</Text>
                <Text style={styles.modalSubtitle}>
                  Your response will be sent privately to the person who asked the question.
                </Text>
                
                <TextInput
                  mode="outlined"
                  placeholder="Type your private response..."
                  value={responseText}
                  onChangeText={setResponseText}
                  style={styles.responseInput}
                  multiline
                  numberOfLines={4}
                  maxLength={500}
                />
                
                <View style={styles.modalButtons}>
                  <Button
                    mode="outlined"
                    onPress={closeResponseModal}
                    style={styles.modalButton}
                  >
                    Cancel
                  </Button>
                  <Button
                    mode="contained"
                    onPress={sendPrivateResponse}
                    style={styles.modalButton}
                    disabled={!responseText.trim()}
                  >
                    Send Response
                  </Button>
                </View>
              </KeyboardAvoidingView>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  chatContainer: {
    flex: 1,
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
  messageRow: {
    flexDirection: 'row',
    marginVertical: 4,
    alignItems: 'flex-end',
  },
  ownMessageRow: {
    justifyContent: 'flex-end',
  },
  otherMessageRow: {
    justifyContent: 'flex-start',
  },
  messageContainer: {
    padding: 12,
    borderRadius: 16,
    maxWidth: '75%',
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
  responseCard: {
    marginVertical: 8,
    backgroundColor: '#e8f5e8',
    borderLeftWidth: 4,
    borderLeftColor: '#4caf50',
  },
  responseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  responseChip: {
    backgroundColor: '#a5d6a7',
  },
  responseTime: {
    fontSize: 10,
    color: '#666',
  },
  responseAuthor: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 4,
  },
  responseContent: {
    fontSize: 14,
    color: '#333',
    marginBottom: 12,
  },
  inputContainer: {
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    minHeight: 70,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 5,
  },
  messageInput: {
    backgroundColor: '#fff',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
    lineHeight: 20,
  },
  responseInput: {
    backgroundColor: '#fff',
    marginBottom: 20,
    minHeight: 100,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  modalButton: {
    flex: 1,
  },
  profilePicture: {
    width: 32,
    height: 32,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 4,
  },
  defaultAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#2196F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
    marginBottom: 4,
  },
  avatarText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});