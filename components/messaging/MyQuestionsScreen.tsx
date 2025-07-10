import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  Text,
  ScrollView,
  RefreshControl,
  Keyboard,
} from 'react-native';
import { Card, Button, Chip, IconButton } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://172.28.119.64:8000';

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
  ride_deleted?: boolean;  // Indicates if the ride post was deleted
  // Detailed status information
  ride_status?: string;  // "active", "full", "completed", "cancelled"
  ride_communities?: string[];  // Communities the ride is available to
  user_can_access?: boolean;  // Whether current user can access this ride
  unavailable_reason?: string;  // Reason why ride is unavailable
}

interface PrivateResponse {
  response_id: string;
  responder_name?: string;
  response: string;
  timestamp: string;
}

interface MyQuestionsScreenProps {
  onBack: () => void;
}

export default function MyQuestionsScreen({ onBack }: MyQuestionsScreenProps) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [responses, setResponses] = useState<{ [key: string]: PrivateResponse[] }>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadQuestions();
  }, []);

  const loadQuestions = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/my-questions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const questionsData: Question[] = await response.json();
        setQuestions(questionsData);
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to load questions');
      }
    } catch (error) {
      console.error('Error loading questions:', error);
      Alert.alert('Error', 'Unable to load questions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadResponses = async (questionId: string) => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/question/${questionId}/responses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const responsesData: PrivateResponse[] = await response.json();
        setResponses(prev => ({
          ...prev,
          [questionId]: responsesData
        }));
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to load responses');
      }
    } catch (error) {
      console.error('Error loading responses:', error);
      Alert.alert('Error', 'Unable to load responses');
    }
  };

  const toggleExpanded = async (questionId: string) => {
    const newExpanded = new Set(expandedQuestions);
    
    if (expandedQuestions.has(questionId)) {
      newExpanded.delete(questionId);
    } else {
      newExpanded.add(questionId);
      // Load responses if not already loaded
      if (!responses[questionId]) {
        await loadResponses(questionId);
      }
    }
    
    setExpandedQuestions(newExpanded);
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
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
  };

  const formatTripInfo = (question: Question) => {
    if (question.ride_deleted) {
      return 'This ride post has been deleted';
    }
    
    if (!question.user_can_access && question.unavailable_reason) {
      const origin = question.ride_origin || 'Unknown';
      const destination = question.ride_destination || 'Unknown';
      const tripRoute = `${origin} → ${destination}`;
      return `${tripRoute} - ${question.unavailable_reason}`;
    }
    
    const origin = question.ride_origin || 'Unknown';
    const destination = question.ride_destination || 'Unknown';
    
    // Format date
    let dateStr = '';
    if (question.departure_date) {
      const date = new Date(question.departure_date);
      dateStr = date.toLocaleDateString('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    }
    
    // Create compact trip description
    const tripRoute = `${origin} → ${destination}`;
    return dateStr ? `${tripRoute}, ${dateStr}` : tripRoute;
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadQuestions();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading your questions...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <IconButton icon="arrow-left" onPress={onBack} />
        <Text style={styles.headerTitle}>My Questions</Text>
        <IconButton icon="refresh" onPress={loadQuestions} />
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        keyboardShouldPersistTaps="handled"
        onScrollBeginDrag={() => Keyboard.dismiss()}
      >
        {questions.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No questions yet</Text>
            <Text style={styles.emptySubtext}>
              Ask questions about rides you're interested in joining!
            </Text>
          </View>
        ) : (
          questions.map(question => (
            <Card key={question.question_id} style={styles.questionCard}>
              <Card.Content>
                <View style={styles.questionHeader}>
                  <View style={styles.statusChips}>
                    {question.ride_deleted ? (
                      <Chip 
                        icon="delete" 
                        style={[styles.statusChip, styles.deletedChip]}
                      >
                        Ride Deleted
                      </Chip>
                    ) : !question.user_can_access ? (
                      <Chip 
                        icon="lock" 
                        style={[styles.statusChip, styles.unavailableChip]}
                      >
                        Unavailable
                      </Chip>
                    ) : (
                      <Chip 
                        icon="help-circle" 
                        style={[
                          styles.statusChip,
                          question.response_count > 0 ? styles.answeredChip : styles.pendingChip
                        ]}
                      >
                        {question.response_count > 0 ? 'Answered' : 'Pending'}
                      </Chip>
                    )}
                  </View>
                  <Text style={styles.questionTime}>
                    {formatTime(question.timestamp)}
                  </Text>
                </View>

                <View style={styles.tripInfo}>
                  <Text style={styles.tripText}>
                    🚗 {formatTripInfo(question)}
                  </Text>
                </View>

                <Text style={styles.questionText}>
                  {question.question}
                </Text>

                {question.response_count > 0 && !question.ride_deleted && (
                  <Button
                    mode="outlined"
                    onPress={() => toggleExpanded(question.question_id)}
                    style={styles.viewResponsesButton}
                    icon={expandedQuestions.has(question.question_id) ? "chevron-up" : "chevron-down"}
                  >
                    {expandedQuestions.has(question.question_id) 
                      ? 'Hide Responses' 
                      : `View ${question.response_count} Response${question.response_count > 1 ? 's' : ''}`
                    }
                  </Button>
                )}

                {question.response_count > 0 && question.ride_deleted && (
                  <Text style={styles.deletedResponseNote}>
                    📄 {question.response_count} response{question.response_count > 1 ? 's' : ''} received before ride was deleted
                  </Text>
                )}

                {expandedQuestions.has(question.question_id) && responses[question.question_id] && (
                  <View style={styles.responsesContainer}>
                    <Text style={styles.responsesTitle}>Responses from ride members:</Text>
                    {responses[question.question_id].map(response => (
                      <View key={response.response_id} style={styles.responseCard}>
                        <View style={styles.responseHeader}>
                          <Text style={styles.responderName}>
                            {response.responder_name || 'Ride Member'}
                          </Text>
                          <Text style={styles.responseTime}>
                            {formatTime(response.timestamp)}
                          </Text>
                        </View>
                        <Text style={styles.responseText}>
                          {response.response}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </Card.Content>
            </Card>
          ))
        )}
      </ScrollView>
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
    marginRight: 48,
  },
  content: {
    flex: 1,
  },
  scrollContent: {
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
    textAlign: 'center',
  },
  questionCard: {
    marginBottom: 16,
  },
  questionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  statusChips: {
    flexDirection: 'row',
    gap: 8,
  },
  statusChip: {
    height: 32,
  },
  answeredChip: {
    backgroundColor: '#c8e6c9',
  },
  pendingChip: {
    backgroundColor: '#ffecb3',
  },
  deletedChip: {
    backgroundColor: '#ffcdd2',
  },
  unavailableChip: {
    backgroundColor: '#fff3e0',
  },
  questionTime: {
    fontSize: 12,
    color: '#666',
  },
  tripInfo: {
    backgroundColor: '#f0f4f8',
    borderRadius: 6,
    padding: 8,
    marginVertical: 8,
  },
  tripText: {
    fontSize: 12,
    color: '#2d3748',
    fontWeight: '500',
  },
  questionText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 16,
    lineHeight: 20,
  },
  viewResponsesButton: {
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  deletedResponseNote: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 6,
  },
  responsesContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  responsesTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  responseCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#2196F3',
  },
  responseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  responderName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  responseTime: {
    fontSize: 10,
    color: '#666',
  },
  responseText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 18,
  },
});