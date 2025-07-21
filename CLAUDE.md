# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (React Native with Expo)
```bash
# Navigate to frontend directory
cd frontend

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

### Backend (FastAPI with Python)
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test email functionality
python test_email.py

# Environment setup (copy and configure)
cp .env.example .env
```

## Project Architecture

**Campus Mobility** is a full-stack ride-sharing application for Claremont Colleges (5C) with separate frontend and backend applications.

### Backend Architecture (FastAPI + MongoDB)

#### Core Technology Stack
- **Framework**: FastAPI with async support
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Email**: SMTP with Gmail integration (HTML templates)
- **External APIs**: Google Places API, Uber API (planned)

#### Database Design
- **users_collection**: User accounts with email verification system
- **rides_collection**: Ride requests and matching
- MongoDB Atlas connection string in `database.py:5`

#### Route Structure
- **users.py**: Authentication, signup, email verification, login
- **rides.py**: Ride request creation and retrieval
- **places.py**: Google Places autocomplete and details

#### Email Verification System
- 6-digit verification codes with 1-hour expiry
- College domain validation for Claremont Colleges (`.edu` domains)
- Professional HTML email templates with Campus Mobility branding
- Graceful fallback to console output when SMTP not configured

#### Key Environment Variables
Set these in `backend/.env`:
- `MONGO_URI`: MongoDB connection string
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Gmail SMTP config
- `GOOGLE_PLACES_API_KEY`: Google Places API key
- `JWT_SECRET_KEY`: JWT token signing key

### Frontend Architecture (React Native + Expo)

#### Core Technology Stack
- **Framework**: React Native 0.79.4 with Expo SDK 53
- **Navigation**: Expo Router (file-based routing) with tab navigation
- **UI**: React Native Paper + custom themed components
- **State**: Local state with AsyncStorage for persistence
- **Location**: Expo Location for GPS and Google Places autocomplete

#### Authentication Flow
1. Email validation (Claremont Colleges `.edu` domains only)
2. College auto-detection from email domain
3. Email verification with 6-digit code
4. JWT token storage in AsyncStorage
5. Conditional rendering between Login screen and authenticated tabs

#### File-Based Routing Structure
- `app/_layout.tsx`: Root layout with auth logic and theme provider
- `app/Login.tsx`: Combined login/signup/verification screen
- `app/(tabs)/`: Tab group with bottom navigation:
  - `index.tsx`: "You" tab (home screen) 
  - `Explore.tsx`: Explore tab
  - `RideShare.tsx`: Ride sharing with destination/time/community selection
  - `FindDrivers.tsx`: Driver finding
  - `FindRiders.tsx`: Rider finding

#### Backend Integration
- **API Base URL**: `http://172.28.119.64:8000/` (hardcoded in components)
- **Endpoints**: `/signup`, `/verify-email`, `/resend-verification`, `/login`
- **Authentication**: JWT tokens with 30-day expiry stored in AsyncStorage

### College System
Supported Claremont Colleges with automatic college assignment:
- Pomona College (`pomona.edu`)
- Harvey Mudd College (`hmc.edu`) 
- Scripps College (`scrippscollege.edu`)
- Pitzer College (`pitzer.edu`)
- Claremont McKenna College (`cmc.edu`)

## Development Workflow

### Running Both Services
1. **Backend**: `cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. **Frontend**: `cd frontend && npx expo start`
3. **Database**: MongoDB Atlas (connection configured in backend)

### Common Development Tasks

#### Adding New API Endpoints
1. Define Pydantic models in `backend/models.py`
2. Create route handlers in appropriate `backend/routes/*.py` file
3. Import and include router in `backend/main.py`

#### Adding New Frontend Screens
Create new files in `frontend/app/` - Expo Router handles routing automatically based on file structure.

#### Email Configuration
1. Set up Gmail App Password (see `backend/EMAIL_SETUP.md`)
2. Configure SMTP variables in `backend/.env`
3. Test with `python backend/test_email.py`

#### Location Services
- Frontend uses Google Places autocomplete via backend proxy
- Configure `GOOGLE_PLACES_API_KEY` in backend environment

### Security Notes
- MongoDB connection string is hardcoded in `database.py` (should be environment variable)
- Frontend uses hardcoded backend IP address (should be configurable)
- CORS is currently set to allow all origins (should be restricted in production)
- No rate limiting implemented on API endpoints

### Testing
- No formal testing framework configured for either frontend or backend
- Manual testing via `backend/test_email.py` for email functionality
- Frontend testing via Expo development tools