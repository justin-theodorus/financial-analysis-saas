# Financial Analysis SaaS

An AI-powered financial analysis platform that combines technical analysis and semantic sentiment analysis to provide comprehensive investment insights for stocks.

## Overview

This full-stack application provides real-time financial analysis through:

- **Technical Analysis**: RSI, MACD, EMA, and other technical indicators using historical market data
- **Semantic Analysis**: News sentiment analysis from Benzinga using Hugging Face transformers
- **AI Insights**: OpenAI-powered investment recommendations combining both analysis types
- **Modern UI**: Beautiful, responsive dashboard built with Next.js and Shadcn UI

## Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **UI Components**: Shadcn UI, Radix UI
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **State Management**: Zustand (optional)
- **Theme**: next-themes with dark mode support

### Backend
- **Framework**: FastAPI (Python)
- **APIs**:
  - Marketstack API (historical stock data)
  - Benzinga API (financial news)
  - OpenAI API (AI insights)
  - Hugging Face (sentiment analysis)
- **Data Processing**: pandas, numpy
- **ML/AI**: Hugging Face transformers, PyTorch
- **Testing**: pytest

## Project Structure

```
financial-analysis-saas/
├── frontend-updated/           # Next.js frontend application
│   ├── app/                   # App Router pages
│   │   ├── dashboard/        # Main dashboard
│   │   ├── market/           # Market sector pages
│   │   └── page.tsx         # Root page (redirects to dashboard)
│   ├── components/           # React components
│   │   ├── kokonutui/       # Custom dashboard components
│   │   └── ui/              # Shadcn UI components
│   ├── lib/                 # Utility functions and API clients
│   └── public/              # Static assets
├── backend/                  # Python FastAPI backend
│   ├── ai_verdict_system.py    # Main API server
│   ├── technical_analyzer.py   # Technical analysis module
│   ├── technical_indicators.py # Technical indicators calculation
│   ├── semantic_analyzer.py    # News sentiment analysis
│   ├── requirements.txt        # Python dependencies
│   └── tests/                  # Test suite
└── README.md                # This file
```

## Features

### 1. Technical Analysis
- Real-time stock price data from Marketstack
- Technical indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - EMA (Exponential Moving Average)
  - Support and resistance levels
  - Trend analysis
- Confidence scoring for trading signals

### 2. Semantic Analysis
- Financial news aggregation from Benzinga
- Sentiment analysis using Hugging Face models
- News scoring (0-10 scale)
- Social media buzz tracking
- Positive/negative/neutral sentiment ratios

### 3. AI Verdict System
- OpenAI GPT-powered insights
- Combined technical + semantic analysis
- Investment recommendations (Buy/Hold/Sell)
- Analyst rating system
- Confidence-weighted verdicts

### 4. Market Sectors
- Technology stocks
- Healthcare stocks
- Financial stocks
- Energy stocks

## Prerequisites

- **Node.js** 18+ and npm/pnpm
- **Python** 3.9+
- **API Keys** (required):
  - Marketstack API key
  - Benzinga API key
  - OpenAI API key
  - Hugging Face token

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd financial-analysis-saas
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MARKETSTACK_API_KEY=your_marketstack_key
BENZINGA_API_KEY=your_benzinga_key
OPENAI_API_KEY=your_openai_key
HUGGING_FACE_TOKEN=your_hf_token
EOF
```

### 3. Frontend Setup

```bash
cd frontend-updated

# Install dependencies
npm install
# or
pnpm install

# Create .env.local (optional, if needed)
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

## Running the Application

### Start the Backend

```bash
cd backend
source venv/bin/activate  # Activate virtual environment
python ai_verdict_system.py
```

The API server will start at `http://localhost:8000`

### Start the Frontend

```bash
cd frontend-updated
npm run dev
# or
pnpm dev
```

The frontend will start at `http://localhost:3000`

## API Endpoints

### Main Endpoints

- `GET /` - API status check
- `GET /health` - Health check with service status
- `GET /test` - Simple connectivity test
- `POST /analyze` - Get complete analysis for a stock symbol
- `POST /analyze/detailed` - Get detailed raw analysis data

### Example Request

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "days_back": 7,
    "technical_interval": "1D",
    "technical_limit": 100
  }'
```

### Response Format

```json
{
  "stock": {
    "symbol": "AAPL",
    "price": 175.50
  },
  "technicalAnalysis": {
    "trend": "Bullish",
    "support": 166.73,
    "resistance": 184.28,
    "rsi": 62.3,
    "macd": "Buy Signal"
  },
  "semanticAnalysis": {
    "sentiment": "Positive",
    "newsScore": 7.2,
    "socialMediaBuzz": "High",
    "analystRating": "Buy"
  },
  "aiInsight": "Based on technical and semantic analysis, AAPL shows bullish momentum with positive market sentiment..."
}
```

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest
```

Test coverage includes:
- Unit tests for technical indicators
- Unit tests for semantic analysis
- Integration tests for API endpoints
- Mock tests for external API calls

### Frontend Testing

```bash
cd frontend-updated
npm run lint
```

## Environment Variables

### Backend (.env)

```env
# Required API Keys
MARKETSTACK_API_KEY=your_key_here
BENZINGA_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
HUGGING_FACE_TOKEN=your_token_here
```

### Frontend (.env.local)

```env
# Optional - defaults to localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Guidelines

### Code Style

- **Frontend**: Follow Standard.js rules (2 spaces, single quotes, no semicolons)
- **Backend**: Follow PEP 8 Python style guide
- **TypeScript**: Strict mode enabled with explicit return types
- **React**: Functional components with hooks only

### Component Structure

- Server Components by default (Next.js App Router)
- Use `'use client'` only when necessary
- Keep files under 200 lines
- Extract reusable logic into custom hooks
- Use composition over inheritance

### State Management

- Lift state up for shared state
- Use Zustand for complex global state
- Prefer Server Components and Server Actions
- Minimize client-side state

## API Rate Limits

- **Marketstack Free**: 1,000 requests/month, 5 requests/second
- **Benzinga**: Varies by plan
- **OpenAI**: Varies by plan
- **Hugging Face**: Inference API limits apply

## Troubleshooting

### Backend Issues

**API Key Errors**
```bash
# Verify .env file exists and contains valid keys
cat backend/.env
```

**Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Port Already in Use**
```bash
# Change port in ai_verdict_system.py
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use different port
```

### Frontend Issues

**CORS Errors**
- Check that backend is running on port 8000
- Verify CORS middleware includes your frontend URL

**API Connection Errors**
- Verify backend is running: `curl http://localhost:8000/health`
- Check `NEXT_PUBLIC_API_URL` in .env.local

**Build Errors**
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```


## Acknowledgments

- [Marketstack](https://marketstack.com/) - Stock market data API
- [Benzinga](https://www.benzinga.com/apis) - Financial news API
- [OpenAI](https://openai.com/) - AI-powered insights
- [Hugging Face](https://huggingface.co/) - Sentiment analysis models
- [Shadcn UI](https://ui.shadcn.com/) - Beautiful UI components
- [Next.js](https://nextjs.org/) - React framework


**Built with ❤️ using Next.js, FastAPI, and AI**

