import pytest
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from semantic_analyzer import FinancialSemanticAnalyzer, clean_data_for_downstream

# Load real environment variables
load_dotenv()

@pytest.mark.integration
class TestFinancialSemanticAnalyzerIntegration:
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with real API keys"""
        benzinga_key = os.getenv('BENZINGA_API_KEY')
        hf_token = os.getenv('HUGGING_FACE_TOKEN')
        
        if not benzinga_key or not hf_token:
            pytest.skip("API credentials not available")
        
        return FinancialSemanticAnalyzer(benzinga_key, hf_token)
    
    def test_real_finbert_sentiment_analysis(self, analyzer):
        """Test FinBERT with real API calls"""
        test_texts = [
            "Apple reported strong quarterly earnings with record revenue growth",
            "Market volatility increases amid economic uncertainty",
            "Company announces new product launch"
        ]
        
        results = analyzer.analyze_sentiment_batch(test_texts, batch_size=3)
        
        # Verify structure
        assert len(results) == 3
        for result in results:
            assert 'sentiment' in result
            assert 'confidence' in result
            assert 'positive_score' in result
            assert 'negative_score' in result
            assert 'neutral_score' in result
            assert result['sentiment'] in ['positive', 'negative', 'neutral']
            assert 0 <= result['confidence'] <= 1
            
        print(f"FinBERT Results: {results}")
    
    def test_real_benzinga_news_fetch(self, analyzer):
        """Test Benzinga news fetching with real API"""
        symbols = ['AAPL']  # Use a reliable stock symbol
        
        news_df = analyzer.get_benzinga_news(symbols, days_back=3)
        
        if not news_df.empty:
            # Verify structure
            required_columns = ['symbol', 'title', 'body', 'created']
            for col in required_columns:
                assert col in news_df.columns
            
            # Verify data quality
            assert all(news_df['symbol'] == 'AAPL')
            assert all(news_df['title'].notna())
            
            print(f"Found {len(news_df)} news articles for AAPL")
            print(f"Sample titles: {news_df['title'].head(2).tolist()}")
        else:
            print("No news found - this might be normal on weekends or holidays")
    
    def test_complete_pipeline_integration(self, analyzer):
        """Test the complete semantic analysis pipeline"""
        symbols = ['AAPL', 'MSFT']
        
        # Run complete analysis
        results = analyzer.process_semantic_analysis(symbols, days_back=5)
        
        if not results.empty:
            # Verify structure
            expected_columns = [
                'symbol', 'news_count', 'overall_sentiment', 
                'weighted_sentiment_avg', 'positive_ratio',
                'negative_ratio', 'neutral_ratio', 'average_confidence'
            ]
            
            for col in expected_columns:
                assert col in results.columns
            
            # Verify data ranges
            assert all(results['positive_ratio'] >= 0)
            assert all(results['positive_ratio'] <= 1)
            assert all(results['negative_ratio'] >= 0)
            assert all(results['negative_ratio'] <= 1)
            assert all(results['neutral_ratio'] >= 0)
            assert all(results['neutral_ratio'] <= 1)
            
            print("Complete Pipeline Results:")
            print(results[['symbol', 'news_count', 'overall_sentiment', 'sentiment_signal']])
            
            # Test downstream processing
            cleaned_data = clean_data_for_downstream(results)
            assert 'sentiment_signal' in cleaned_data.columns
            assert 'confidence_normalized' in cleaned_data.columns
            
        else:
            print("No results - might be due to no news availability")
