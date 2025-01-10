[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Profile Views](https://visitor-badge.laobi.icu/badge?page_id=ahmed5145.ahmed5145&title=Profile%20Views)
[![GitHub stars](https://img.shields.io/github/stars/ahmed5145/chessmate.svg)](https://github.com/ahmed5145/chessmate/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ahmed5145/chessmate.svg)](https://github.com/ahmed5145/chessmate/network)
[![GitHub issues](https://img.shields.io/github/issues/ahmed5145/chessmate.svg)](https://github.com/ahmed5145/chessmate/issues)
![GitHub last commit](https://img.shields.io/github/last-commit/ahmed5145/chessmate)

# ChessMate

ChessMate is a web application that analyzes chess games from chess.com and lichess to provide personalized insights and improvement recommendations.

## Features

- Game analysis from chess.com and lichess profiles
- Detailed metrics on time management, opening performance, tactics, and resourcefulness, endgames
- Customizable analysis packages (50-1000 games)
- Downloadable analysis reports (PDF/CSV)
- Personalized improvement recommendations
- User dashboard with analysis history

## Tech Stack

- Frontend: React.js
- Backend: Django
- Database: PostgreSQL/MongoDB
- Authentication: OAuth, JWT
- Payment: Stripe/PayPal
- Analysis: python-chess, Stockfish

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ahmed5145/chessmate.git
cd chessmate
```

2. Install dependencies:
```bash
# Backend
cd chessmate
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run development servers:
```bash
# Backend
cd chess_mate
python manage.py migrate
python manage.py runserver

# Frontend
npm start
```

## Usage

1. Create an account
2. Select an analysis package
3. Choose games for analysis
4. Complete payment
5. View detailed analysis in your dashboard


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to branch (`git push origin feature/name`)
5. Create Pull Request

## License

[MIT License](LICENSE)

## Contact

For support or questions, reach out to ahmedmohamed200354@gmail.com

## Roadmap

- Real-time game analysis
- AI-powered coaching
- Community features
- Mobile application

---
*Document generated on January 3, 2025*  
*Copyright © 2025 ChessMate. All rights reserved.*
