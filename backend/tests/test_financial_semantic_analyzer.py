import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests_mock
import os
from dotenv import load_dotenv

# Assuming your analyzer is in semantic_analyzer.py
from semantic_analyzer import FinancialSemanticAnalyzer, clean_data_for_downstream

class TestFinancialSemanticAnalyzer:
    
    @pytest.fixture(autouse=True)
    def setup_env_vars(self, monkeypatch):
        """Setup environment variables for testing"""
        monkeypatch.setenv("BENZINGA_API_KEY", "test_benzinga_key")
        monkeypatch.setenv("HUGGING_FACE_TOKEN", "test_hf_token")
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        # Pass the required arguments to the constructor
        return FinancialSemanticAnalyzer("test_benzinga_key", "test_hf_token")
    
    @pytest.fixture
    def sample_benzinga_response(self):
        """Sample Benzinga API response"""
        return {
            "data": [
                {
                    "title": "Apple Reports Strong Q3 Earnings",
                    "body": "Apple Inc. reported better-than-expected quarterly earnings with strong iPhone sales driving revenue growth.",
                    "created": "2025-07-24T10:30:00Z",
                    "url": "https://example.com/apple-earnings",
                    "author": "Financial Reporter"
                },
                {
                    "title": "Market Volatility Concerns Rise",
                    "body": "Investors are concerned about increased market volatility amid economic uncertainty.",
                    "created": "2025-07-24T09:15:00Z", 
                    "url": "https://example.com/market-volatility",
                    "author": "Market Analyst"
                }
            ]
        }
    
    @pytest.fixture
    def sample_finbert_response(self):
        """Sample FinBERT API response structure"""
        return [
            Mock(label='positive', score=0.7),
            Mock(label='neutral', score=0.2),
            Mock(label='negative', score=0.1)
        ]
    
    def test_initialization_success(self):
        """Test successful initialization with valid API keys"""
        with patch.object(FinancialSemanticAnalyzer, 'setup_finbert_inference'):
            analyzer = FinancialSemanticAnalyzer("test_benzinga_key", "test_hf_token")
            assert analyzer.benzinga_api_key == "test_benzinga_key"
            assert analyzer.hf_token == "test_hf_token"
    
    def test_initialization_with_none_values(self):
        """Test initialization with None values"""
        with patch.object(FinancialSemanticAnalyzer, 'setup_finbert_inference'):
            analyzer = FinancialSemanticAnalyzer(None, None)
            assert analyzer.benzinga_api_key is None
            assert analyzer.hf_token is None
    
    @patch('semantic_analyzer.InferenceClient')
    def test_setup_finbert_inference_success(self, mock_client, analyzer):
        """Test successful FinBERT inference setup"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        analyzer.setup_finbert_inference()
        
        mock_client.assert_called_once_with(
            model="ProsusAI/finbert",
            token="test_hf_token"
        )
        assert analyzer.client == mock_client_instance
    
    @patch('semantic_analyzer.InferenceClient')
    def test_setup_finbert_inference_failure(self, mock_client, analyzer, capsys):
        """Test FinBERT inference setup failure"""
        mock_client.side_effect = Exception("Connection failed")
        
        analyzer.setup_finbert_inference()
        
        captured = capsys.readouterr()
        assert "Error initializing FinBERT Inference API: Connection failed" in captured.out
    
    def test_get_benzinga_news_success(self, analyzer, sample_benzinga_response):
        """Test successful Benzinga news fetching"""
        with requests_mock.Mocker() as m:
            m.get('https://api.benzinga.com/api/v2/news', json=sample_benzinga_response)
            
            result = analyzer.get_benzinga_news(['AAPL'], days_back=7)
            
            assert len(result) == 2
            assert result.iloc[0]['symbol'] == 'AAPL'
            assert result.iloc[0]['title'] == "Apple Reports Strong Q3 Earnings"
            assert 'body' in result.columns
            assert 'created' in result.columns
    
    def test_get_benzinga_news_api_error(self, analyzer, capsys):
        """Test Benzinga news fetching with API error"""
        with requests_mock.Mocker() as m:
            m.get('https://api.benzinga.com/api/v2/news', status_code=500)
            
            result = analyzer.get_benzinga_news(['AAPL'], days_back=7)
            
            assert result.empty
            captured = capsys.readouterr()
            assert "Error fetching news for AAPL" in captured.out
    
    def test_get_benzinga_news_empty_response(self, analyzer):
        """Test Benzinga news fetching with empty response"""
        with requests_mock.Mocker() as m:
            m.get('https://api.benzinga.com/api/v2/news', json={"data": []})
            
            result = analyzer.get_benzinga_news(['AAPL'], days_back=7)
            
            assert result.empty
    
    def test_analyze_sentiment_batch_success(self, analyzer, sample_finbert_response):
        """Test successful sentiment analysis"""
        analyzer.client = Mock()
        analyzer.client.text_classification.return_value = sample_finbert_response
        
        texts = ["Apple earnings are strong", "Market volatility increases"]
        result = analyzer.analyze_sentiment_batch(texts)
        
        assert len(result) == 2
        assert result[0]['sentiment'] == 'positive'
        assert result[0]['confidence'] == 0.7
        assert result[0]['positive_score'] == 0.7
        assert result[0]['negative_score'] == 0.1
        assert result[0]['neutral_score'] == 0.2
        assert 'weighted_sentiment' in result[0]
    
    def test_analyze_sentiment_batch_empty_input(self, analyzer):
        """Test sentiment analysis with empty input"""
        result = analyzer.analyze_sentiment_batch([])
        assert result == []
    
    def test_analyze_sentiment_batch_api_error(self, analyzer, capsys):
        """Test sentiment analysis with API error"""
        analyzer.client = Mock()
        analyzer.client.text_classification.side_effect = Exception("API Error")
        
        texts = ["Test text"]
        result = analyzer.analyze_sentiment_batch(texts)
        
        assert len(result) == 1
        assert result[0]['sentiment'] == 'neutral'
        assert result[0]['confidence'] == 0.0
        captured = capsys.readouterr()
        assert "Error in batch sentiment analysis" in captured.out
    
    def test_calculate_sentiment_scores_mixed_sentiments(self, analyzer):
        """Test sentiment score calculation with mixed sentiments"""
        sentiment_results = [
            {
                'sentiment': 'positive',
                'confidence': 0.8,
                'positive_score': 0.8,
                'negative_score': 0.1,
                'neutral_score': 0.1,
                'weighted_sentiment': 0.7
            },
            {
                'sentiment': 'negative', 
                'confidence': 0.6,
                'positive_score': 0.2,
                'negative_score': 0.6,
                'neutral_score': 0.2,
                'weighted_sentiment': -0.4
            },
            {
                'sentiment': 'neutral',
                'confidence': 0.7,
                'positive_score': 0.3,
                'negative_score': 0.2,
                'neutral_score': 0.7,
                'weighted_sentiment': 0.1
            }
        ]
        
        result = analyzer.calculate_sentiment_scores(sentiment_results)
        
        assert 'overall_sentiment' in result
        assert 'weighted_sentiment_avg' in result
        assert result['positive_ratio'] == 1/3
        assert result['negative_ratio'] == 1/3
        assert result['neutral_ratio'] == 1/3
        assert result['average_confidence'] == 0.7
        assert 'sentiment_momentum' in result
    
    def test_calculate_sentiment_scores_empty_input(self, analyzer):
        """Test sentiment score calculation with empty input"""
        result = analyzer.calculate_sentiment_scores([])
        
        expected_keys = [
            'overall_sentiment', 'weighted_sentiment_avg', 'positive_ratio',
            'negative_ratio', 'neutral_ratio', 'average_confidence',
            'sentiment_momentum', 'avg_positive_score', 'avg_negative_score',
            'avg_neutral_score'
        ]
        
        for key in expected_keys:
            assert key in result
            assert result[key] == 0.0
    
    @patch.object(FinancialSemanticAnalyzer, 'get_benzinga_news')
    @patch.object(FinancialSemanticAnalyzer, 'analyze_sentiment_batch')
    def test_process_semantic_analysis_success(self, mock_sentiment, mock_news, analyzer):
        """Test complete semantic analysis process"""
        # Mock news data
        mock_news_df = pd.DataFrame([
            {
                'symbol': 'AAPL',
                'title': 'Apple Earnings',
                'body': 'Strong performance',
                'created': '2025-07-24T10:00:00Z'
            }
        ])
        mock_news.return_value = mock_news_df
        
        # Mock sentiment results
        mock_sentiment.return_value = [{
            'sentiment': 'positive',
            'confidence': 0.8,
            'positive_score': 0.8,
            'negative_score': 0.1,
            'neutral_score': 0.1,
            'weighted_sentiment': 0.7
        }]
        
        result = analyzer.process_semantic_analysis(['AAPL'])
        
        assert len(result) == 1
        assert result.iloc[0]['symbol'] == 'AAPL'
        assert result.iloc[0]['news_count'] == 1
        assert 'overall_sentiment' in result.columns
        assert 'analysis_date' in result.columns
    
    @patch.object(FinancialSemanticAnalyzer, 'get_benzinga_news')
    def test_process_semantic_analysis_no_news(self, mock_news, analyzer):
        """Test semantic analysis with no news data"""
        mock_news.return_value = pd.DataFrame()
        
        result = analyzer.process_semantic_analysis(['AAPL'])
        
        assert result.empty
    
    def test_clean_data_for_downstream_success(self):
        """Test data cleaning for downstream processing"""
        semantic_results = pd.DataFrame([
            {
                'symbol': 'AAPL',
                'overall_sentiment': 0.5,
                'weighted_sentiment_avg': 0.4,
                'positive_ratio': 0.6,
                'negative_ratio': 0.2,
                'average_confidence': 0.8
            }
        ])
        
        result = clean_data_for_downstream(semantic_results)
        
        assert 'sentiment_signal' in result.columns
        assert 'confidence_normalized' in result.columns
        assert result.iloc[0]['sentiment_signal'] == 1  # Positive signal
        assert result.iloc[0]['confidence_normalized'] == 1.0
    
    def test_clean_data_for_downstream_missing_columns(self):
        """Test data cleaning with missing columns"""
        semantic_results = pd.DataFrame([{'symbol': 'AAPL'}])
        
        result = clean_data_for_downstream(semantic_results)
        
        required_columns = [
            'symbol', 'overall_sentiment', 'weighted_sentiment_avg',
            'positive_ratio', 'negative_ratio', 'average_confidence'
        ]
        
        for col in required_columns:
            assert col in result.columns
    
    def test_clean_data_for_downstream_neutral_signal(self):
        """Test data cleaning generates neutral signal"""
        semantic_results = pd.DataFrame([
            {
                'symbol': 'AAPL',
                'overall_sentiment': 0.05,
                'weighted_sentiment_avg': 0.05,
                'positive_ratio': 0.4,
                'negative_ratio': 0.3,
                'average_confidence': 0.6
            }
        ])
        
        result = clean_data_for_downstream(semantic_results)
        
        assert result.iloc[0]['sentiment_signal'] == 0  # Neutral signal
    
    def test_clean_data_for_downstream_negative_signal(self):
        """Test data cleaning generates negative signal"""
        semantic_results = pd.DataFrame([
            {
                'symbol': 'AAPL',
                'overall_sentiment': -0.3,
                'weighted_sentiment_avg': -0.2,
                'positive_ratio': 0.2,
                'negative_ratio': 0.7,
                'average_confidence': 0.8
            }
        ])
        
        result = clean_data_for_downstream(semantic_results)
        
        assert result.iloc[0]['sentiment_signal'] == -1  # Negative signal

class TestIntegration:
    """Integration tests for end-to-end functionality"""
    
    @patch('semantic_analyzer.InferenceClient')
    def test_full_pipeline_integration(self, mock_client):
        """Test complete pipeline from initialization to cleaned output"""
        # Setup mocks
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        # Mock FinBERT response
        mock_client_instance.text_classification.return_value = [
            Mock(label='positive', score=0.7),
            Mock(label='neutral', score=0.2),
            Mock(label='negative', score=0.1)
        ]
        
        # Mock Benzinga response
        benzinga_response = {
            "data": [{
                "title": "Test News",
                "body": "Test content",
                "created": "2025-07-24T10:00:00Z",
                "url": "https://test.com",
                "author": "Test Author"
            }]
        }
        
        with requests_mock.Mocker() as m:
            m.get('https://api.benzinga.com/api/v2/news', json=benzinga_response)
            
            # Run full pipeline - pass required arguments
            analyzer = FinancialSemanticAnalyzer("test_key", "test_token")
            semantic_results = analyzer.process_semantic_analysis(['AAPL'])
            cleaned_data = clean_data_for_downstream(semantic_results)
            
            # Verify results
            assert len(cleaned_data) == 1
            assert cleaned_data.iloc[0]['symbol'] == 'AAPL'
            assert 'sentiment_signal' in cleaned_data.columns
            assert 'confidence_normalized' in cleaned_data.columns
