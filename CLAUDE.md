# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
npm install

# Start development server
npx expo start

# Platform-specific development
npx expo start --android    # Android emulator
npx expo start --ios        # iOS simulator  
npx expo start --web        # Web browser

# Code quality
npx expo lint               # Run ESLint
```

## Project Architecture

This is a **Campus Mobility** React Native application built with Expo SDK 53, targeting college ride-sharing between Claremont Colleges (5C).

### Core Architecture
- **Framework**: React Native with Expo Router (file-based routing)
- **Navigation**: Tab-based navigation with authentication gate
- **UI**: React Native Paper + custom themed components (ThemedText, ThemedView)
- **State**: Local state with useState, AsyncStorage for auth persistence
- **Authentication**: Token-based with conditional rendering (Login ↔ Tabs)

### File-Based Routing Structure
- `app/_layout.tsx` - Root layout with auth logic and theme provider
- `app/Login.tsx` - Authentication screen 
- `app/(tabs)/` - Tab group with bottom navigation:
  - `index.tsx` - "You" tab (home screen)
  - `Explore.tsx` - Explore tab
  - `UberShare.tsx` - Ride sharing with destination/time/community selection
  - `FindDrivers.tsx` - Driver finding
  - `FindRiders.tsx` - Rider finding
  - `_layout.tsx` - Tab layout configuration

### Key Dependencies
- **React Native**: 0.79.4 with New Architecture enabled
- **Expo Router**: ~5.1.0 for navigation
- **React Native Paper**: ^5.14.5 for Material Design components
- **AsyncStorage**: ^2.2.0 for data persistence

### Authentication Flow
1. **Email Verification System**: Only `.edu` emails from Claremont Colleges accepted
2. **Sign Up Flow**: Email validation → College detection → Verification code sent
3. **Email Verification**: 6-digit code with 1-hour expiry
4. **Login Flow**: Email/password → JWT token stored in AsyncStorage
5. **College Assignment**: Users automatically assigned to college based on email domain
6. **Index Screen**: Handles all auth states (login/signup/verification/authenticated)

### Theme System
- Light/dark mode with automatic detection
- Colors defined in `/constants/Colors.ts`
- Platform-specific styling (iOS/Android differences)
- Custom themed components in `/components/`

### Backend Integration
- **API Base**: `http://172.28.119.64:8000/`
- **Endpoints**: `/signup`, `/verify-email`, `/resend-verification`, `/login`
- **Authentication**: JWT tokens with 30-day expiry
- **College Domains**: `pomona.edu`, `hmc.edu`, `scrippscollege.edu`, `pitzer.edu`, `cmc.edu`

## Development Notes

### Adding New Screens
Create new files in `app/` directory - Expo Router automatically handles routing based on file structure.

### Component Patterns
Use ThemedText and ThemedView for consistent styling across light/dark modes. Follow existing patterns in tabs for UI components and navigation.

### TypeScript Configuration
Strict mode enabled with path mapping (`@/*` to project root). Expo provides typed routes when `typed-routes` is enabled in app.json.

### No Testing Framework
Currently no Jest or testing libraries configured. Consider adding React Native Testing Library for future test coverage.