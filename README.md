[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Profile Views](https://visitor-badge.laobi.icu/badge?page_id=ahmed5145.ahmed5145&title=Profile%20Views)
[![GitHub stars](https://img.shields.io/github/stars/ahmed5145/chessmate.svg)](https://github.com/ahmed5145/chessmate/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ahmed5145/chessmate.svg)](https://github.com/ahmed5145/chessmate/network)
[![GitHub issues](https://img.shields.io/github/issues/ahmed5145/chessmate.svg)](https://github.com/ahmed5145/chessmate/issues)
![GitHub last commit](https://img.shields.io/github/last-commit/ahmed5145/chessmate)

# ChessMate - Chess Coaching Platform

> **Note:** This repo is the early public build of ChessMate. The production system — live at [chess-mate.online](https://chess-mate.online) — is developed in a private repo. Architecture, tradeoffs, and current state are covered in the [case study](https://ahmedmohamedh.vercel.app/work/case-study).

ChessMate is a chess coaching platform that uses the Stockfish engine to analyze batches of games and generate personalized coaching reports.

## Navigation
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

- **Game Analysis**: Batch analysis of chess games using the Stockfish engine
- **Personalized Feedback**: Coaching feedback generated from your own games
- **Credit System**: Flexible credit packages for game analysis
- **Multi-Platform Support**: Import games from Chess.com and Lichess
- **Modern UI**: Responsive design with real-time updates
- **Secure Authentication**: JWT-based authentication system

## Prerequisites

- Python 3.8+
- Node.js 14+
- Redis Server
- Stockfish Chess Engine
- PostgreSQL (optional, SQLite by default)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ahmed5145/chessmate.git
   cd chessmate
   ```

2. **Install dependencies**:
   - **Backend**:
     ```bash
     cd chessmate
     python -m venv venv
     source venv/bin/activate  # or `venv\Scripts\activate` on Windows
     pip install -r requirements.txt
     ```

   - **Frontend**:
     ```bash
     cd frontend
     npm install
     ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   # - Set up email credentials
   # - Add OpenAI API key
   # - Configure Stripe keys
   # - Set Stockfish path
   ```

4. **Initialize the database**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Start Redis Server**:
   ```bash
   redis-server
   ```

6. **Start Celery Worker**:
   ```bash
   celery -A chess_mate worker -l info
   ```

7. **Run development servers**:
   - **Backend**:
     ```bash
     cd chess_mate
     python manage.py runserver
     ```

   - **Frontend**:
     ```bash
     cd frontend
     npm start
     ```

## Usage

1. **Create an account** or sign in using your email and password
2. **Purchase analysis credits** from available packages
3. **Import games** from Chess.com or Lichess
4. **Select games** for analysis
5. **View detailed analysis** including:
   - Move accuracy
   - Critical moments
   - Improvement suggestions
   - Opening recommendations
   - Time management feedback

## Testing

- **Backend Tests**:
  ```bash
  cd chess_mate
  python -m pytest
  ```

- **Frontend Tests**:
  ```bash
  cd frontend
  npm test
  ```

## API Documentation

See [API Documentation](docs/api.md) for detailed endpoint information.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Stockfish Chess Engine
- OpenAI API
- Chess.com API
- Lichess API

---
*Copyright © 2024 ChessMate. All rights reserved.*
