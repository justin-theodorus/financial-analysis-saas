import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import numpy as np
from huggingface_hub import InferenceClient
import warnings
warnings.filterwarnings('ignore')

class FinancialSemanticAnalyzer:
    def __init__(self, benzinga_api_key, hf_token):
        """
        Initialize the Financial Semantic Analyzer with FinBERT Inference API
        
        Args:
            benzinga_api_key (str): API key for Benzinga data access
            hf_token (str): Hugging Face API token
        """
        self.benzinga_api_key = benzinga_api_key
        self.hf_token = hf_token
        self.setup_finbert_inference()
        
    def setup_finbert_inference(self):
        """Setup FinBERT inference client"""
        try:
            # Initialize Hugging Face Inference Client
            self.client = InferenceClient(
                model="ProsusAI/finbert",
                token=self.hf_token
            )
            print("FinBERT Inference API client initialized successfully")
            
        except Exception as e:
            print(f"Error initializing FinBERT Inference API: {e}")
    
    def analyze_sentiment_batch(self, texts, batch_size=10):
        """
        Perform sentiment analysis using Hugging Face Inference API
        
        Args:
            texts (list): List of text strings to analyze
            batch_size (int): Number of texts to process in each batch
            
        Returns:
            list: Sentiment analysis results with scores
        """
        if not texts:
            return []
        
        results = []
        
        # Process texts in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            try:
                batch_results = []
                
                for text in batch_texts:
                    # Truncate text to reasonable length for API
                    truncated_text = text[:512] if len(text) > 512 else text
                    
                    response = self.client.text_classification(
                        text=truncated_text,
                        model="ProsusAI/finbert"
                    )
                    
                    # Process the response - handle TextClassificationOutputElement objects
                    if response and len(response) > 0:
                        # Extract scores for each sentiment
                        sentiment_scores = {}
                        
                        for element in response:
                            # Handle both object attributes and dictionary access
                            if hasattr(element, 'label') and hasattr(element, 'score'):
                                label = element.label
                                score = element.score
                            else:
                                label = element.get('label', 'neutral')
                                score = element.get('score', 0.0)
                            
                            sentiment_scores[label.lower()] = score
                        
                        # Get the sentiment with highest confidence
                        best_sentiment = max(sentiment_scores.keys(), key=lambda k: sentiment_scores[k])
                        best_score = sentiment_scores[best_sentiment]
                        
                        # Calculate a weighted sentiment score using all three scores
                        positive_score = sentiment_scores.get('positive', 0.0)
                        negative_score = sentiment_scores.get('negative', 0.0)
                        neutral_score = sentiment_scores.get('neutral', 0.0)
                        
                        # Weighted sentiment: positive contributes +1, negative -1, neutral 0
                        weighted_sentiment = (positive_score * 1.0) + (negative_score * -1.0) + (neutral_score * 0.0)
                        
                        batch_results.append({
                            'sentiment': best_sentiment,
                            'confidence': best_score,
                            'positive_score': positive_score,
                            'negative_score': negative_score,
                            'neutral_score': neutral_score,
                            'weighted_sentiment': weighted_sentiment
                        })
                    else:
                        batch_results.append({
                            'sentiment': 'neutral',
                            'confidence': 0.0,
                            'positive_score': 0.0,
                            'negative_score': 0.0,
                            'neutral_score': 1.0,
                            'weighted_sentiment': 0.0
                        })
                
                results.extend(batch_results)
                
                # Small delay between batches to respect rate limits
                if i + batch_size < len(texts):
                    import time
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error in batch sentiment analysis: {e}")
                # Add neutral results for failed batch
                for _ in batch_texts:
                    results.append({
                        'sentiment': 'neutral',
                        'confidence': 0.0,
                        'positive_score': 0.0,
                        'negative_score': 0.0,
                        'neutral_score': 1.0,
                        'weighted_sentiment': 0.0
                    })
        
        return results

    def get_benzinga_news(self, symbols, days_back=7):
        """
        Fetch news data from Benzinga API within specified timeframe
        
        Args:
            symbols (list): List of stock symbols
            days_back (int): Number of days to look back for news
            
        Returns:
            pandas.DataFrame: News data with timestamps and content
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        news_data = []
        
        for symbol in symbols:
            url = "https://api.benzinga.com/api/v2/news"
            
            params = {
                'token': self.benzinga_api_key,
                'tickers': symbol,
                'dateFrom': start_date.strftime('%Y-%m-%d'),
                'dateTo': end_date.strftime('%Y-%m-%d'),
                'pageSize': 100,
                "displayOutput": "abstract"
            }
            
            
            headers = {
                'accept': 'application/json'
            }
            
            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                
                if isinstance(data, dict):
                    articles = data.get('data', [])
                elif isinstance(data, list):
                    articles = data
                else:
                    print(f"Unexpected Benzinga response format for {symbol}")
                    continue
                
                for article in data.get('data', []):
                    news_data.append({
                        'symbol': symbol,
                        'title': article.get('title', ''),
                        'body': article.get('body', ''),
                        'created': article.get('created', ''),
                        'url': article.get('url', ''),
                        'author': article.get('author', '')
                    })
                    
            except requests.RequestException as e:
                print(f"Error fetching news for {symbol}: {e}")
            except ValueError as e:  # JSON decode error
                print(f"JSON parsing error for {symbol}: {e}")
                print(f"Response content-type: {response.headers.get('content-type')}")
                print(f"Response text (first 200 chars): {response.text[:200]}")
                
        return pd.DataFrame(news_data)
    
    def calculate_sentiment_scores(self, sentiment_results):
        """
        Calculate numerical sentiment scores from FinBERT results
        
        Args:
            sentiment_results (list): Results from sentiment analysis
            
        Returns:
            dict: Aggregated sentiment metrics
        """
        if not sentiment_results:
            return {
                'overall_sentiment': 0.0,
                'weighted_sentiment_avg': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'average_confidence': 0.0,
                'sentiment_momentum': 0.0,
                'avg_positive_score': 0.0,
                'avg_negative_score': 0.0,
                'avg_neutral_score': 0.0
            }
        
        # Extract all metrics
        weighted_sentiments = [r['weighted_sentiment'] for r in sentiment_results]
        confidences = [r['confidence'] for r in sentiment_results]
        positive_scores = [r['positive_score'] for r in sentiment_results]
        negative_scores = [r['negative_score'] for r in sentiment_results]
        neutral_scores = [r['neutral_score'] for r in sentiment_results]
        
        # Count sentiment categories
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for result in sentiment_results:
            sentiment_counts[result['sentiment']] += 1
        
        total_count = len(sentiment_results)
        
        return {
            'overall_sentiment': np.mean([r['confidence'] if r['sentiment'] == 'positive' 
                                        else -r['confidence'] if r['sentiment'] == 'negative' 
                                        else 0 for r in sentiment_results]),
            'weighted_sentiment_avg': np.mean(weighted_sentiments),
            'positive_ratio': sentiment_counts['positive'] / total_count,
            'negative_ratio': sentiment_counts['negative'] / total_count,
            'neutral_ratio': sentiment_counts['neutral'] / total_count,
            'average_confidence': np.mean(confidences),
            'sentiment_momentum': np.std(weighted_sentiments),
            'avg_positive_score': np.mean(positive_scores),
            'avg_negative_score': np.mean(negative_scores),
            'avg_neutral_score': np.mean(neutral_scores)
        }
    
    def process_semantic_analysis(self, symbols, days_back=7):
        """
        Complete semantic analysis pipeline for given symbols
        
        Args:
            symbols (list): Stock symbols to analyze
            days_back (int): Days of news history to analyze
            
        Returns:
            pandas.DataFrame: Processed semantic analysis results
        """
        print(f"Starting semantic analysis for {symbols}")
        
        # Step 1: Get news data from Benzinga
        print("Fetching news data from Benzinga...")
        news_df = self.get_benzinga_news(symbols, days_back)
        
        if news_df.empty:
            print("No news data found")
            return pd.DataFrame()
        
        print(f"Found {len(news_df)} news articles")
        
        # Step 2: Prepare text for sentiment analysis
        news_df['combined_text'] = news_df['title'] + ' ' + news_df['body'].fillna('')
        
        # Step 3: Perform sentiment analysis using FinBERT Inference API
        print("Performing sentiment analysis with FinBERT Inference API...")
        texts = news_df['combined_text'].tolist()
        sentiment_results = self.analyze_sentiment_batch(texts)
        
        # Step 4: Add sentiment results to dataframe
        sentiment_df = pd.DataFrame(sentiment_results)
        news_df = pd.concat([news_df.reset_index(drop=True), sentiment_df], axis=1)
        
        # Step 5: Aggregate results by symbol
        print("Aggregating sentiment scores by symbol...")
        symbol_analysis = []
        
        for symbol in symbols:
            symbol_news = news_df[news_df['symbol'] == symbol]
            
            if not symbol_news.empty:
                symbol_sentiments = sentiment_results[len(symbol_analysis) * len(symbol_news.index):(len(symbol_analysis) + 1) * len(symbol_news.index)]
                sentiment_metrics = self.calculate_sentiment_scores(symbol_sentiments)
                
                symbol_analysis.append({
                    'symbol': symbol,
                    'news_count': len(symbol_news),
                    'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                    **sentiment_metrics
                })
            else:
                # Default neutral sentiment if no news found
                symbol_analysis.append({
                    'symbol': symbol,
                    'news_count': 0,
                    'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                    'overall_sentiment': 0.0,
                    'weighted_sentiment_avg': 0.0,
                    'positive_ratio': 0.0,
                    'negative_ratio': 0.0,
                    'neutral_ratio': 1.0,
                    'average_confidence': 0.0,
                    'sentiment_momentum': 0.0,
                    'avg_positive_score': 0.0,
                    'avg_negative_score': 0.0,
                    'avg_neutral_score': 1.0
                })
        
        results_df = pd.DataFrame(symbol_analysis)
        print("Semantic analysis completed")
        
        return results_df

def clean_data_for_downstream(semantic_results, price_data=None):
    """
    Clean and prepare semantic analysis results for TA-Lib integration
    
    Args:
        semantic_results (pd.DataFrame): Results from semantic analysis
        price_data (pd.DataFrame): Optional price data for integration
        
    Returns:
        pd.DataFrame: Cleaned data ready for technical analysis
    """
    # Ensure we have the required columns
    required_columns = [
        'symbol', 'overall_sentiment', 'weighted_sentiment_avg', 
        'positive_ratio', 'negative_ratio', 'average_confidence'
    ]
    
    for col in required_columns:
        if col not in semantic_results.columns:
            semantic_results[col] = 0.0
    
    # Add sentiment signal for technical analysis integration
    semantic_results['sentiment_signal'] = semantic_results.apply(
        lambda row: 1 if row['weighted_sentiment_avg'] > 0.1 else 
                   (-1 if row['weighted_sentiment_avg'] < -0.1 else 0), 
        axis=1
    )
    
    # Normalize confidence scores
    if semantic_results['average_confidence'].max() > 0:
        semantic_results['confidence_normalized'] = (
            semantic_results['average_confidence'] / 
            semantic_results['average_confidence'].max()
        )
    else:
        semantic_results['confidence_normalized'] = 0.0
    
    return semantic_results
