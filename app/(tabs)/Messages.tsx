import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  Text,
  ScrollView,
  RefreshControl,
  Modal,
  TouchableOpacity,
} from 'react-native';
import { Card, Button, Chip, IconButton, Badge, Divider } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import GroupChatScreen from '@/components/messaging/GroupChatScreen';
import MyQuestionsScreen from '@/components/messaging/MyQuestionsScreen';

const API_BASE_URL = 'http://172.28.119.64:8000';

interface RideWithMessages {
  ride_id: string;
  ride_destination: string;
  ride_origin: string;
  departure_date: string;
  message_count: number;
  last_message_time?: string;
  unread_count?: number;
}

interface Question {
  question_id: string;
  asker_email: string;
  asker_name?: string;
  question: string;
  timestamp: string;
  response_count: number;
  // Trip information
  ride_id: string;
  ride_origin?: string;
  ride_destination?: string;
  departure_date?: string;
}

type ModalContent = 'group-chat' | 'my-questions' | null;

export default function MessagesScreen() {
  const [userRideChats, setUserRideChats] = useState<RideWithMessages[]>([]);
  const [userQuestions, setUserQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalContent, setModalContent] = useState<ModalContent>(null);
  const [selectedRideId, setSelectedRideId] = useState<string | null>(null);

  useEffect(() => {
    loadMessagesData();
  }, []);

  const loadMessagesData = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      // Load user's rides and questions in parallel
      const [ridesResponse, questionsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/my-ride-chats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE_URL}/my-questions`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (questionsResponse.ok) {
        const questions: Question[] = await questionsResponse.json();
        setUserQuestions(questions);
      }

      if (ridesResponse.ok) {
        const rides: RideWithMessages[] = await ridesResponse.json();
        setUserRideChats(rides);
      } else {
        const error = await ridesResponse.json();
        console.error('Failed to load ride chats:', error);
      }

    } catch (error) {
      console.error('Error loading messages data:', error);
      Alert.alert('Error', 'Unable to load messages');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getCurrentUserEmail = async (): Promise<string> => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        const user = JSON.parse(userData);
        return user.email;
      }
    } catch (error) {
      console.error('Error getting user email:', error);
    }
    return '';
  };

  const openGroupChat = (rideId: string) => {
    setSelectedRideId(rideId);
    setModalContent('group-chat');
  };

  const openMyQuestions = () => {
    setModalContent('my-questions');
  };

  const closeModal = () => {
    setModalContent(null);
    setSelectedRideId(null);
    loadMessagesData(); // Refresh data when closing modal
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadMessagesData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading messages...</Text>
      </View>
    );
  }

  return (
    <>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Messages</Text>
          <IconButton
            icon="refresh"
            size={24}
            onPress={onRefresh}
          />
        </View>

        {/* My Questions Section */}
        <View style={styles.section}>
          <TouchableOpacity onPress={openMyQuestions} style={styles.sectionHeader}>
            <View style={styles.sectionTitleContainer}>
              <Text style={styles.sectionTitle}>My Questions</Text>
              {userQuestions.length > 0 && (
                <Badge size={20} style={styles.badge}>
                  {userQuestions.length}
                </Badge>
              )}
            </View>
            <IconButton icon="chevron-right" size={20} />
          </TouchableOpacity>
          
          <Text style={styles.sectionSubtext}>
            Questions you've asked about rides and their responses
          </Text>
        </View>

        <Divider style={styles.divider} />

        {/* Ride Group Chats Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Ride Chats</Text>
          <Text style={styles.sectionSubtext}>
            Group chats for rides you've joined
          </Text>
        </View>

        {userRideChats.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No ride chats yet</Text>
            <Text style={styles.emptySubtext}>
              Join a ride to start chatting with other members!
            </Text>
            <Button
              mode="outlined"
              onPress={() => {/* Navigate to Explore tab */}}
              style={styles.exploreButton}
              icon="magnify"
            >
              Explore Rides
            </Button>
          </View>
        ) : (
          userRideChats.map((rideChat) => (
            <TouchableOpacity
              key={rideChat.ride_id}
              onPress={() => openGroupChat(rideChat.ride_id)}
            >
              <Card style={styles.chatCard}>
                <Card.Content>
                  <View style={styles.chatHeader}>
                    <View style={styles.chatInfo}>
                      <Text style={styles.destination}>
                        {rideChat.ride_origin} → {rideChat.ride_destination}
                      </Text>
                      <Text style={styles.departureDate}>
                        {formatDate(rideChat.departure_date)}
                      </Text>
                    </View>
                    
                    <View style={styles.chatStats}>
                      {rideChat.unread_count && rideChat.unread_count > 0 && (
                        <Badge size={24} style={styles.unreadBadge}>
                          {rideChat.unread_count}
                        </Badge>
                      )}
                      <IconButton icon="chevron-right" size={20} />
                    </View>
                  </View>
                  
                  <View style={styles.chatFooter}>
                    <Text style={styles.messageCount}>
                      {rideChat.message_count} message{rideChat.message_count !== 1 ? 's' : ''}
                    </Text>
                    {rideChat.last_message_time && (
                      <Text style={styles.lastMessageTime}>
                        Last activity: {formatDate(rideChat.last_message_time)}
                      </Text>
                    )}
                  </View>
                </Card.Content>
              </Card>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>

      {/* Modals */}
      <Modal
        visible={modalContent === 'group-chat'}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        {selectedRideId && (
          <GroupChatScreen
            rideId={selectedRideId}
            onBack={closeModal}
          />
        )}
      </Modal>

      <Modal
        visible={modalContent === 'my-questions'}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <MyQuestionsScreen onBack={closeModal} />
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    paddingBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  section: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  sectionSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  badge: {
    backgroundColor: '#2196F3',
  },
  divider: {
    height: 1,
    backgroundColor: '#e0e0e0',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginBottom: 20,
  },
  exploreButton: {
    paddingHorizontal: 20,
  },
  chatCard: {
    margin: 16,
    marginBottom: 8,
    elevation: 2,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  chatInfo: {
    flex: 1,
  },
  destination: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  departureDate: {
    fontSize: 14,
    color: '#666',
  },
  chatStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  unreadBadge: {
    backgroundColor: '#f44336',
    marginRight: 8,
  },
  chatFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  messageCount: {
    fontSize: 12,
    color: '#2196F3',
    fontWeight: 'bold',
  },
  lastMessageTime: {
    fontSize: 12,
    color: '#999',
  },
});