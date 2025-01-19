# ChessMate API Documentation

## Table of Contents
- [Authentication](#authentication)
- [Games](#games)
- [Analysis](#analysis)
- [Credits](#credits)
- [User Management](#user-management)

## Authentication

### Register
```http
POST /api/register
```

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "message": "Registration successful! Please check your email to verify your account.",
  "email": "string"
}
```

**Error Responses:**
```json
{
  "error": "This email is already registered. Please use a different email or try logging in.",
  "field": "email"
}
```
```json
{
  "error": "This username is already taken. Please choose a different username.",
  "field": "username"
}
```

### Email Verification
```http
GET /verify-email/{uidb64}/{token}/
```

Verify email address. Returns HTML pages for success/error.

**Success Response:**
- Renders verification_success.html with login button
- Redirects to frontend login page

**Error Response:**
- Renders verification_error.html with error details
- Provides link to registration page

### Login
```http
POST /api/login
```

Login with email and password.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "message": "Login successful!",
  "tokens": {
    "access": "string",
    "refresh": "string"
  },
  "user": {
    "username": "string",
    "email": "string"
  }
}
```

**Error Responses:**
```json
{
  "error": "Please verify your email before logging in."
}
```
```json
{
  "error": "Invalid email or password."
}
```

### Logout
```http
POST /api/logout
```

Logout and blacklist the refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "message": "Logout successful!"
}
```

## Games

### Fetch Games
```http
POST /api/games/fetch
```

Fetch games from Chess.com or Lichess.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "platform": "chess.com | lichess",
  "username": "string",
  "game_mode": "all | bullet | blitz | rapid | classical",
  "num_games": "integer"
}
```

**Response:**
```json
{
  "message": "Successfully fetched and saved games!",
  "games_saved": "integer",
  "credits_deducted": "integer",
  "credits_remaining": "integer",
  "games": [
    {
      "id": "integer",
      "platform": "string",
      "white": "string",
      "black": "string",
      "opponent": "string",
      "result": "string",
      "date_played": "datetime",
      "opening_name": "string",
      "game_id": "string"
    }
  ]
}
```

### Get User Games
```http
GET /api/games/user
```

Get list of games for the authenticated user.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
```
platform: all | chess.com | lichess (optional)
```

**Response:**
```json
{
  "games": [
    {
      "id": "integer",
      "white": "string",
      "black": "string",
      "result": "string",
      "date_played": "datetime",
      "platform": "string",
      "analysis": "object | null"
    }
  ]
}
```

## Analysis

### Analyze Game
```http
GET/POST /api/analysis/{game_id}
```

Analyze a specific game.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (POST only):**
```json
{
  "depth": "integer (optional, default: 20)",
  "use_ai": "boolean (optional, default: true)"
}
```

**Response:**
```json
{
  "message": "Analysis completed successfully!",
  "analysis": {
    "moves": [
      {
        "move_number": "integer",
        "move": "string",
        "score": "float",
        "is_mistake": "boolean",
        "is_blunder": "boolean",
        "time_spent": "float"
      }
    ]
  },
  "feedback": {
    "opening": {
      "accuracy": "float",
      "played_moves": ["string"],
      "suggestions": ["string"]
    },
    "tactics": {
      "missed_opportunities": ["string"],
      "suggestions": ["string"]
    },
    "mistakes": "integer",
    "blunders": "integer",
    "inaccuracies": "integer",
    "time_management": {
      "time_pressure_moves": ["integer"],
      "suggestions": ["string"]
    },
    "strengths": [
      {
        "area": "string",
        "description": "string"
      }
    ],
    "improvement_areas": [
      {
        "area": "string",
        "description": "string"
      }
    ],
    "ai_suggestions": "string | object"
  },
  "credits_remaining": "integer"
}
```

### Batch Analysis
```http
POST /api/analysis/batch
```

Analyze multiple games.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "num_games": "integer",
  "use_ai": "boolean (optional, default: true)",
  "depth": "integer (optional, default: 20)"
}
```

**Response:**
```json
{
  "message": "Batch analysis completed!",
  "results": {
    "individual_games": {
      "game_id": {
        "blunders": "integer",
        "mistakes": "integer",
        "inaccuracies": "integer",
        "opening": {
          "accuracy": "float",
          "played_moves": ["string"]
        },
        "time_management": {
          "time_pressure_moves": ["integer"]
        }
      }
    },
    "overall_stats": {
      "total_games": "integer",
      "wins": "integer",
      "losses": "integer",
      "draws": "integer",
      "average_accuracy": "float",
      "common_mistakes": {
        "blunders": "float",
        "mistakes": "float",
        "inaccuracies": "float",
        "time_pressure": "float"
      },
      "improvement_areas": [
        {
          "area": "string",
          "description": "string"
        }
      ],
      "strengths": [
        {
          "area": "string",
          "description": "string"
        }
      ]
    },
    "dynamic_feedback": "string | object"
  }
}
```

## Dashboard

### Get Dashboard Data
```http
GET /api/dashboard
```

Get user-specific games and statistics for the dashboard.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "total_games": "integer",
  "analyzed_games": "integer",
  "unanalyzed_games": "integer",
  "statistics": {
    "wins": "integer",
    "losses": "integer",
    "draws": "integer",
    "win_rate": "float"
  },
  "recent_games": [
    {
      "id": "integer",
      "platform": "string",
      "white": "string",
      "black": "string",
      "opponent": "string",
      "result": "string",
      "date_played": "datetime",
      "opening_name": "string",
      "analysis": "object | null"
    }
  ]
}
```

## Credits

### Get Credits
```http
GET /api/credits
```

Get current credit balance.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "credits": "integer"
}
```

### Purchase Credits
```http
POST /api/credits/purchase
```

Create a checkout session for credit purchase.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "package_id": "string"
}
```

**Response:**
```json
{
  "success": true,
  "checkout_url": "string",
  "session_id": "string"
}
```

### Confirm Purchase
```http
POST /api/credits/confirm
```

Confirm credit purchase and add credits.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "session_id": "string"
}
```

**Response:**
```json
{
  "success": true,
  "credits": "integer",
  "added_credits": "integer"
}
```

## User Management

### Get Profile
```http
GET /api/user/profile
```

Get user profile information.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "username": "string",
  "email": "string",
  "rating": "integer",
  "total_games": "integer",
  "preferred_openings": ["string"],
  "credits": "integer"
}
```

### Update Profile
```http
PUT /api/user/profile
```

Update user profile information.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "rating": "integer (optional)",
  "preferred_openings": ["string"] (optional)
}
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "profile": {
    "username": "string",
    "email": "string",
    "rating": "integer",
    "total_games": "integer",
    "preferred_openings": ["string"],
    "credits": "integer"
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Error message describing the issue"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication credentials were not provided"
}
```

### 403 Forbidden
```json
{
  "error": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
  "error": "Requested resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error occurred",
  "details": "Optional error details"
}
```

## Rate Limiting

Most endpoints are rate-limited to prevent abuse. The current limits are:

- Authentication endpoints: 5 requests per minute
- Game fetching: 10 requests per minute
- Analysis endpoints: 3 requests per minute
- Credit operations: 5 requests per minute

When rate limit is exceeded, you'll receive a 429 Too Many Requests response:
```json
{
  "error": "Too many requests. Please try again later."
}
``` 