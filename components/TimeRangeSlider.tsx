import React, { useState, useRef } from 'react';
import {
  View,
  StyleSheet,
  Text,
} from 'react-native';
import {
  PanGestureHandler,
  GestureHandlerRootView,
  PanGestureHandlerGestureEvent,
} from 'react-native-gesture-handler';
import Animated, {
  useAnimatedGestureHandler,
  useAnimatedStyle,
  useSharedValue,
  runOnJS,
  clamp,
} from 'react-native-reanimated';

interface TimeRangeSliderProps {
  earliestTime: number; // Time in minutes from midnight (0-1440)
  latestTime: number;   // Time in minutes from midnight (0-1440)
  onTimeChange: (earliest: number, latest: number) => void;
}

const SLIDER_WIDTH = 280;
const HANDLE_SIZE = 24;
const TRACK_HEIGHT = 4;
const MIN_RANGE = 30; // Minimum 30 minutes between earliest and latest

export default function TimeRangeSlider({
  earliestTime,
  latestTime,
  onTimeChange,
}: TimeRangeSliderProps) {
  const earliestPosition = useSharedValue((earliestTime / 1440) * SLIDER_WIDTH);
  const latestPosition = useSharedValue((latestTime / 1440) * SLIDER_WIDTH);

  const formatTime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours === 0 ? 12 : hours > 12 ? hours - 12 : hours;
    return `${displayHours}:${mins.toString().padStart(2, '0')} ${period}`;
  };

  const positionToTime = (position: number): number => {
    return Math.round((position / SLIDER_WIDTH) * 1440);
  };

  const updateTimes = (earliestPos: number, latestPos: number) => {
    const earliest = positionToTime(earliestPos);
    const latest = positionToTime(latestPos);
    onTimeChange(earliest, latest);
  };

  const earliestGestureHandler = useAnimatedGestureHandler<PanGestureHandlerGestureEvent>({
    onStart: (_, context) => {
      context.startX = earliestPosition.value;
    },
    onActive: (event, context) => {
      const newPosition = clamp(
        context.startX + event.translationX,
        0,
        Math.min(latestPosition.value - (MIN_RANGE / 1440) * SLIDER_WIDTH, SLIDER_WIDTH)
      );
      earliestPosition.value = newPosition;
    },
    onEnd: () => {
      runOnJS(updateTimes)(earliestPosition.value, latestPosition.value);
    },
  });

  const latestGestureHandler = useAnimatedGestureHandler<PanGestureHandlerGestureEvent>({
    onStart: (_, context) => {
      context.startX = latestPosition.value;
    },
    onActive: (event, context) => {
      const newPosition = clamp(
        context.startX + event.translationX,
        Math.max(earliestPosition.value + (MIN_RANGE / 1440) * SLIDER_WIDTH, 0),
        SLIDER_WIDTH
      );
      latestPosition.value = newPosition;
    },
    onEnd: () => {
      runOnJS(updateTimes)(earliestPosition.value, latestPosition.value);
    },
  });

  const earliestHandleStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: earliestPosition.value - HANDLE_SIZE / 2 }],
  }));

  const latestHandleStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: latestPosition.value - HANDLE_SIZE / 2 }],
  }));

  const rangeStyle = useAnimatedStyle(() => ({
    left: earliestPosition.value,
    width: latestPosition.value - earliestPosition.value,
  }));

  return (
    <GestureHandlerRootView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.label}>Departure Time Range</Text>
        <View style={styles.timeContainer}>
          <Text style={styles.timeText}>
            {formatTime(earliestTime)} - {formatTime(latestTime)}
          </Text>
        </View>
      </View>

      <View style={styles.sliderContainer}>
        {/* Track */}
        <View style={styles.track} />
        
        {/* Active range */}
        <Animated.View style={[styles.activeTrack, rangeStyle]} />

        {/* Time markers */}
        <View style={styles.markersContainer}>
          {[6, 9, 12, 15, 18, 21].map((hour) => {
            const position = ((hour * 60) / 1440) * SLIDER_WIDTH;
            return (
              <View
                key={hour}
                style={[styles.marker, { left: position }]}
              >
                <View style={styles.markerTick} />
                <Text style={styles.markerText}>
                  {hour > 12 ? `${hour - 12}PM` : hour === 12 ? '12PM' : `${hour}AM`}
                </Text>
              </View>
            );
          })}
        </View>

        {/* Earliest time handle */}
        <PanGestureHandler onGestureEvent={earliestGestureHandler}>
          <Animated.View style={[styles.handle, styles.earliestHandle, earliestHandleStyle]}>
            <View style={styles.handleInner}>
              <Text style={styles.handleText}>E</Text>
            </View>
          </Animated.View>
        </PanGestureHandler>

        {/* Latest time handle */}
        <PanGestureHandler onGestureEvent={latestGestureHandler}>
          <Animated.View style={[styles.handle, styles.latestHandle, latestHandleStyle]}>
            <View style={styles.handleInner}>
              <Text style={styles.handleText}>L</Text>
            </View>
          </Animated.View>
        </PanGestureHandler>
      </View>

      <View style={styles.legendContainer}>
        <View style={styles.legendItem}>
          <View style={[styles.legendCircle, styles.earliestHandle]} />
          <Text style={styles.legendText}>Earliest</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendCircle, styles.latestHandle]} />
          <Text style={styles.legendText}>Latest</Text>
        </View>
      </View>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 20,
    paddingHorizontal: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    marginBottom: 16,
  },
  header: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  timeContainer: {
    alignItems: 'center',
  },
  timeText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  sliderContainer: {
    height: 60,
    justifyContent: 'center',
    marginBottom: 20,
  },
  track: {
    height: TRACK_HEIGHT,
    backgroundColor: '#e0e0e0',
    borderRadius: TRACK_HEIGHT / 2,
    width: SLIDER_WIDTH,
  },
  activeTrack: {
    position: 'absolute',
    height: TRACK_HEIGHT,
    backgroundColor: '#4CAF50',
    borderRadius: TRACK_HEIGHT / 2,
  },
  markersContainer: {
    position: 'absolute',
    top: TRACK_HEIGHT + 8,
    width: SLIDER_WIDTH,
    height: 20,
  },
  marker: {
    position: 'absolute',
    alignItems: 'center',
  },
  markerTick: {
    width: 1,
    height: 6,
    backgroundColor: '#ccc',
    marginBottom: 2,
  },
  markerText: {
    fontSize: 10,
    color: '#666',
  },
  handle: {
    position: 'absolute',
    width: HANDLE_SIZE,
    height: HANDLE_SIZE,
    borderRadius: HANDLE_SIZE / 2,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  earliestHandle: {
    backgroundColor: '#2196F3',
  },
  latestHandle: {
    backgroundColor: '#FF9800',
  },
  handleInner: {
    width: '100%',
    height: '100%',
    borderRadius: HANDLE_SIZE / 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  handleText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  legendContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendCircle: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 12,
    color: '#666',
  },
});