# ChessMate API Documentation

## Authentication Endpoints

### POST /api/register/
Register a new user account.
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```
Response: User details and token

### POST /api/login/
Login to existing account.
```json
{
  "username": "string",
  "password": "string"
}
```
Response: Authentication token

### POST /api/token/refresh/
Refresh an expired token.
```json
{
  "refresh": "string"
}
```
Response: New access token

## Game Management

### GET /api/games/
Fetch user's saved games.

Response: List of games with analysis status

### POST /api/games/fetch/
Fetch games from external platforms.
```json
{
  "platform": "chess.com|lichess",
  "username": "string"
}
```
Response: Number of games fetched

### POST /api/games/{id}/analyze/
Analyze a specific game.
```json
{
  "use_ai": boolean (optional)
}
```
Response: Detailed game analysis and feedback

### POST /api/games/batch-analyze/
Analyze multiple games.
```json
{
  "num_games": integer,
  "use_ai": boolean (optional)
}
```
Response: Batch analysis results

## Credit System

### GET /api/credits/
Get current user's credit balance.

Response: Credit balance

### POST /api/credits/deduct/
Deduct credits for game analysis.
```json
{
  "amount": integer
}
```
Response: Updated credit balance

### POST /api/purchase-credits/
Initialize credit purchase.
```json
{
  "package_id": "string"
}
```
Response: Stripe payment intent

### POST /api/confirm-purchase/
Confirm credit purchase after payment.
```json
{
  "payment_intent_id": "string"
}
```
Response: Updated credit balance

## Error Responses

All endpoints may return the following error responses:

- 400: Bad Request - Invalid input
- 401: Unauthorized - Authentication required
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource not found
- 500: Internal Server Error

## Rate Limiting

- API requests are limited to 100 requests per minute per user
- Analysis endpoints are limited to 10 requests per minute per user

## Authentication

All endpoints except /api/register/ and /api/login/ require authentication via Bearer token:

```
Authorization: Bearer <access_token>
``` 