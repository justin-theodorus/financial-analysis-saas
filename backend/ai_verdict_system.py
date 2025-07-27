import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import openai
from dotenv import load_dotenv
import traceback


# Import your analysis modules
from technical_analyzer import TechnicalAnalyzer
from technical_indicators import TechnicalIndicators, Signal
from semantic_analyzer import FinancialSemanticAnalyzer, clean_data_for_downstream


# Load with explicit path
load_dotenv()

class AnalysisRequest(BaseModel):
    symbol: str
    days_back: Optional[int] = 7
    technical_interval: Optional[str] = "1D"
    technical_limit: Optional[int] = 100
    
    class Config:
        # Allow extra fields to be ignored instead of causing validation errors
        extra = "ignore"


class StockInfo(BaseModel):
    symbol: str
    price: float


class TechnicalAnalysisResponse(BaseModel):
    trend: str
    support: float
    resistance: float
    rsi: float
    macd: str


class SemanticAnalysisResponse(BaseModel):
    sentiment: str
    newsScore: float
    socialMediaBuzz: str
    analystRating: str


class FrontendCompatibleResponse(BaseModel):
    stock: StockInfo
    technicalAnalysis: TechnicalAnalysisResponse
    semanticAnalysis: SemanticAnalysisResponse
    aiInsight: str


class AIVerdictSystem:
    """
    AI-powered system that combines technical and semantic analysis 
    to generate investment verdicts using OpenAI
    """
    
    def __init__(self):
        # Initialize OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize analyzers
        self.technical_analyzer = TechnicalAnalyzer()
        self.technical_indicators = TechnicalIndicators()
        
        # Initialize semantic analyzer
        benzinga_key = os.getenv("BENZINGA_API_KEY")
        hf_token = os.getenv("HUGGING_FACE_TOKEN")
        
        if not benzinga_key or not hf_token:
            raise ValueError("BENZINGA_API_KEY and HUGGING_FACE_TOKEN required")
            
        self.semantic_analyzer = FinancialSemanticAnalyzer(benzinga_key, hf_token)
        
        # OpenAI model configuration
        self.openai_model = "gpt-4"  # Use gpt-3.5-turbo for cost efficiency if needed
        
    def run_technical_analysis(self, symbols: List[str], interval: str = "1D", limit: int = 100) -> Dict[str, Any]:
        """Run complete technical analysis for given symbols"""
        try:
            # Get historical data
            historical_data = self.technical_analyzer.get_historical_data(
                symbols=symbols,
                interval=interval,
                limit=limit
            )
            
            if historical_data.empty:
                return {"error": "No historical data retrieved", "results": {}}
            
            # Perform technical analysis
            analysis_results = self.technical_indicators.analyze_portfolio(historical_data)
            
            # Convert results to JSON-serializable format
            json_results = {}
            for symbol, result in analysis_results.items():
                json_results[symbol] = {
                    "symbol": result.symbol,
                    "current_price": result.current_price,
                    "overall_signal": result.overall_signal.name,
                    "overall_confidence": result.overall_confidence,
                    "recommendation": result.recommendation,
                    "datetime": result.datetime.isoformat(),
                    "indicators": [
                        {
                            "name": ind.name,
                            "signal": ind.signal.name,
                            "value": ind.value,
                            "confidence": ind.confidence,
                            "description": ind.description
                        }
                        for ind in result.indicators
                    ]
                }
            
            return {"error": None, "results": json_results}
            
        except Exception as e:
            return {"error": str(e), "results": {}}
    
    def run_semantic_analysis(self, symbols: List[str], days_back: int = 7) -> Dict[str, Any]:
        """Run semantic analysis for given symbols"""
        try:
            # Perform semantic analysis
            semantic_results = self.semantic_analyzer.process_semantic_analysis(
                symbols=symbols,
                days_back=days_back
            )
            
            if semantic_results.empty:
                return {"error": "No semantic data retrieved", "results": {}}
            
            # Clean data for integration
            cleaned_results = clean_data_for_downstream(semantic_results)
            
            # Convert to JSON-serializable format
            json_results = {}
            for _, row in cleaned_results.iterrows():
                symbol = row['symbol']
                json_results[symbol] = {
                    "symbol": symbol,
                    "news_count": int(row['news_count']),
                    "overall_sentiment": float(row['overall_sentiment']),
                    "weighted_sentiment_avg": float(row['weighted_sentiment_avg']),
                    "positive_ratio": float(row['positive_ratio']),
                    "negative_ratio": float(row['negative_ratio']),
                    "neutral_ratio": float(row['neutral_ratio']),
                    "average_confidence": float(row['average_confidence']),
                    "sentiment_signal": int(row['sentiment_signal']),
                    "confidence_normalized": float(row['confidence_normalized'])
                }
            
            return {"error": None, "results": json_results}
            
        except Exception as e:
            return {"error": str(e), "results": {}}
    
    def generate_ai_insight(self, symbol: str, technical_data: Dict, semantic_data: Dict, 
                           current_price: float) -> str:
        """Generate AI insight text for the frontend"""
        
        prompt = f"""
        Generate a concise, professional investment insight for {symbol} based on the following analysis data.
        Keep it to 2-3 sentences and make it sound like expert analysis.
        
        Current Price: ${current_price:.2f}
        Technical Analysis: {json.dumps(technical_data, indent=2)}
        Semantic Analysis: {json.dumps(semantic_data, indent=2)}
        
        Format as a single paragraph insight that explains the key findings and outlook.
        """
        
        try:
            # Use the newer OpenAI client format
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using faster model for simple insight generation
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial analyst providing brief, professional market insights."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ OpenAI API call failed: {e}")
            # Fallback insight
            trend = technical_data.get('overall_signal', 'NEUTRAL')
            sentiment = 'positive' if semantic_data.get('weighted_sentiment_avg', 0) > 0 else 'negative' if semantic_data.get('weighted_sentiment_avg', 0) < 0 else 'neutral'
            
            return f"Based on technical and semantic analysis, {symbol} shows {trend.lower()} momentum with {sentiment} market sentiment. Current technical indicators suggest {trend.lower()} bias while news sentiment analysis indicates {sentiment} market perception."
    
    def format_for_frontend(self, symbol: str, technical_results: Dict, semantic_results: Dict) -> FrontendCompatibleResponse:
        """Convert analysis results to frontend-compatible format"""
        
        # Get data for the specific symbol
        tech_data = technical_results.get(symbol, {})
        sem_data = semantic_results.get(symbol, {})
        
        # Extract current price
        current_price = tech_data.get('current_price', 0.0)
        
        # Extract technical indicators
        indicators = tech_data.get('indicators', [])
        rsi_indicator = next((ind for ind in indicators if ind['name'] == 'RSI'), None)
        macd_indicator = next((ind for ind in indicators if ind['name'] == 'MACD'), None)
        ema_indicator = next((ind for ind in indicators if ind['name'] == 'EMA'), None)
        
        # Determine trend
        overall_signal = tech_data.get('overall_signal', 'HOLD')
        trend_map = {'BUY': 'Bullish', 'SELL': 'Bearish', 'HOLD': 'Neutral'}
        trend = trend_map.get(overall_signal, 'Neutral')
        
        # Calculate support and resistance levels
        support = current_price * 0.95  # 5% below current price
        resistance = current_price * 1.05  # 5% above current price
        
        # Format MACD signal
        macd_signal = "Buy Signal" if macd_indicator and macd_indicator['signal'] == 'BUY' else "Sell Signal" if macd_indicator and macd_indicator['signal'] == 'SELL' else "Neutral"
        
        # Convert sentiment to frontend format
        sentiment_score = sem_data.get('weighted_sentiment_avg', 0.0)
        if sentiment_score > 0.1:
            sentiment = "Positive"
        elif sentiment_score < -0.1:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        
        # Calculate news score (convert to 0-10 scale)
        positive_ratio = sem_data.get('positive_ratio', 0.0)
        confidence = sem_data.get('average_confidence', 0.0)
        news_score = min(10.0, max(0.0, (positive_ratio * 10.0 + confidence * 5.0) / 1.5))
        
        # Determine social media buzz
        news_count = sem_data.get('news_count', 0)
        if news_count > 20:
            social_buzz = "High"
        elif news_count > 10:
            social_buzz = "Medium"
        else:
            social_buzz = "Low"
        
        # Determine analyst rating
        overall_confidence = tech_data.get('overall_confidence', 0.0)
        if overall_signal == 'BUY' and overall_confidence > 70:
            analyst_rating = "Strong Buy"
        elif overall_signal == 'BUY':
            analyst_rating = "Buy"
        elif overall_signal == 'SELL' and overall_confidence > 70:
            analyst_rating = "Strong Sell"
        elif overall_signal == 'SELL':
            analyst_rating = "Sell"
        else:
            analyst_rating = "Hold"
        
        # Generate AI insight
        ai_insight = self.generate_ai_insight(symbol, tech_data, sem_data, current_price)
        
        return FrontendCompatibleResponse(
            stock=StockInfo(
                symbol=symbol,
                price=current_price
            ),
            technicalAnalysis=TechnicalAnalysisResponse(
                trend=trend,
                support=round(support, 2),
                resistance=round(resistance, 2),
                rsi=round(rsi_indicator['value'], 1) if rsi_indicator else 50.0,
                macd=macd_signal
            ),
            semanticAnalysis=SemanticAnalysisResponse(
                sentiment=sentiment,
                newsScore=round(news_score, 1),
                socialMediaBuzz=social_buzz,
                analystRating=analyst_rating
            ),
            aiInsight=ai_insight
        )
    
    async def get_complete_verdict(self, symbol: str, days_back: int = 7, 
                                 technical_interval: str = "1D", technical_limit: int = 100) -> FrontendCompatibleResponse:
        """Main method to get complete analysis verdict in frontend format"""
        
        print(f"Starting complete analysis for symbol: {symbol}")
        
        # Run technical analysis
        print("Running technical analysis...")
        technical_results = self.run_technical_analysis(
            symbols=[symbol],
            interval=technical_interval,
            limit=technical_limit
        )
        
        # Run semantic analysis
        print("Running semantic analysis...")
        semantic_results = self.run_semantic_analysis(
            symbols=[symbol],
            days_back=days_back
        )
        
        # Check for errors and provide defaults if needed
        tech_data = technical_results.get("results", {})
        sem_data = semantic_results.get("results", {})
        
        # If no data available, provide reasonable defaults
        if not tech_data.get(symbol):
            tech_data[symbol] = {
                'current_price': 100.0,  # Default price
                'overall_signal': 'HOLD',
                'overall_confidence': 50.0,
                'indicators': [
                    {'name': 'RSI', 'value': 50.0, 'signal': 'HOLD'},
                    {'name': 'MACD', 'value': 0.0, 'signal': 'HOLD'},
                    {'name': 'EMA', 'value': 100.0, 'signal': 'HOLD'}
                ]
            }
        
        if not sem_data.get(symbol):
            sem_data[symbol] = {
                'weighted_sentiment_avg': 0.0,
                'positive_ratio': 0.5,
                'average_confidence': 0.5,
                'news_count': 5
            }
        
        # Format for frontend
        frontend_response = self.format_for_frontend(symbol, tech_data, sem_data)
        
        print("Analysis complete!")
        return frontend_response


# Initialize FastAPI app
app = FastAPI(
    title="AI Financial Verdict System", 
    version="1.0.0",
    description="AI-powered financial analysis system compatible with React frontend"
)

# ADD CORS MIDDLEWARE FIRST (order matters!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default port
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative React port
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",  # Vite with 127.0.0.1
        "http://localhost:4173",  # Vite preview port
        "http://localhost:8080",  # Your current frontend port
        "http://127.0.0.1:8080",  # Your current frontend port with 127.0.0.1
        # Add your production frontend URL here when deployed
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add middleware to log all requests for debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"🌐 {request.method} {request.url} from {request.client.host if request.client else 'unknown'}")
    print(f"🔧 Headers: {dict(request.headers)}")
    response = await call_next(request)
    print(f"📤 Response status: {response.status_code}")
    return response


# Initialize the verdict system
try:
    verdict_system = AIVerdictSystem()
    print("✓ AI Verdict System initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize AI Verdict System: {e}")
    verdict_system = None


@app.get("/")
async def root():
    return {"message": "AI Financial Verdict System", "status": "running"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if verdict_system else "error",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "technical_analyzer": verdict_system is not None,
            "semantic_analyzer": verdict_system is not None,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "marketstack": bool(os.getenv("MARKETSTACK_API_KEY")),
            "benzinga": bool(os.getenv("BENZINGA_API_KEY")),
            "huggingface": bool(os.getenv("HUGGING_FACE_TOKEN"))
        }
    }


@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify CORS and connectivity"""
    return {"message": "Backend is working!", "timestamp": datetime.now().isoformat()}



@app.post("/analyze", response_model=FrontendCompatibleResponse)
async def get_financial_verdict(request: Request):
    """
    Main endpoint to get AI-powered financial verdict
    in format compatible with React frontend
    """
    
    if not verdict_system:
        raise HTTPException(status_code=500, detail="AI Verdict System not initialized")
    
    try:
        # Get raw request body for debugging
        body = await request.body()
        print(f"📩 Raw request body: {body.decode()}")
        
        # Check if body is empty (shouldn't happen for POST, but let's be safe)
        if not body:
            raise HTTPException(status_code=400, detail="Request body is empty")
        
        # Parse JSON manually to get better error handling
        try:
            request_data = json.loads(body.decode())
            print(f"📋 Parsed request data: {request_data}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
        
        # Validate and create request object
        try:
            analysis_request = AnalysisRequest(**request_data)
            print(f"✅ Successfully created AnalysisRequest: {analysis_request}")
        except ValidationError as e:
            print(f"❌ Pydantic validation error: {e}")
            # Return more detailed validation error
            error_details = []
            for error in e.errors():
                error_details.append(f"{error['loc'][0]}: {error['msg']}")
            raise HTTPException(status_code=400, detail=f"Validation error: {'; '.join(error_details)}")
        
        # Basic validation
        if not analysis_request.symbol or not analysis_request.symbol.strip():
            raise HTTPException(status_code=400, detail="Symbol is required and cannot be empty")
        
        # Clean and validate symbol
        symbol = analysis_request.symbol.strip().upper()
        if len(symbol) > 10:
            raise HTTPException(status_code=400, detail=f"Symbol too long: {symbol} (max 10 characters)")
        
        print(f"🔍 Analyzing symbol: {symbol}")
    
        # Get complete analysis
        response = await verdict_system.get_complete_verdict(
            symbol=symbol,
            days_back=analysis_request.days_back or 7,
            technical_interval=analysis_request.technical_interval or "1D",
            technical_limit=analysis_request.technical_limit or 100
        )
        
        print(f"✅ Analysis completed for {symbol}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# Legacy endpoint for backward compatibility (if needed)
@app.post("/analyze/detailed")
async def get_detailed_analysis(request: AnalysisRequest):
    """
    Legacy endpoint that returns complete raw analysis data
    """
    
    if not verdict_system:
        raise HTTPException(status_code=500, detail="AI Verdict System not initialized")
    
    if not request.symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    try:
        # Run both analyses
        technical_results = verdict_system.run_technical_analysis(
            symbols=[request.symbol.upper()],
            interval=request.technical_interval,
            limit=request.technical_limit
        )
        
        semantic_results = verdict_system.run_semantic_analysis(
            symbols=[request.symbol.upper()],
            days_back=request.days_back
        )
        
        return {
            "symbol": request.symbol.upper(),
            "analysis_timestamp": datetime.now().isoformat(),
            "technical_analysis": technical_results,
            "semantic_analysis": semantic_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
