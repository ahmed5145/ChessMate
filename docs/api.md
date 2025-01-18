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
POST /api/auth/register
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
  "message": "User registered successfully! Please confirm your email."
}
```

### Login
```http
POST /api/auth/login
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
  }
}
```

### Logout
```http
POST /api/auth/logout
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
  "credits_remaining": "integer"
}
```

### Get Saved Games
```http
GET /api/games/saved
```

Get list of saved games.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "id": "integer",
    "opponent": "string",
    "result": "string",
    "played_at": "datetime",
    "game_url": "string",
    "opening_name": "string",
    "is_white": "boolean",
    "analysis": "object | null"
  }
]
```

## Analysis

### Analyze Game
```http
POST /api/analysis/game/{game_id}
```

Analyze a specific game.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "depth": "integer (optional, default: 20)",
  "use_ai": "boolean (optional, default: true)"
}
```

**Response:**
```json
{
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
      "analysis": "string",
      "suggestions": ["string"]
    },
    "tactics": {
      "analysis": "string",
      "suggestions": ["string"]
    },
    "strategy": {
      "analysis": "string",
      "suggestions": ["string"]
    },
    "time_management": {
      "analysis": "string",
      "suggestions": ["string"]
    },
    "endgame": {
      "analysis": "string",
      "suggestions": ["string"]
    },
    "study_plan": {
      "focus_areas": ["string"],
      "exercises": ["string"]
    }
  }
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
        "analysis": "object",
        "feedback": "object"
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
    "dynamic_feedback": "object"
  }
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