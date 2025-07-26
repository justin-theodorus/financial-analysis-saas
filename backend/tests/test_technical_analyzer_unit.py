import pytest
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import requests_mock

from technical_analyzer import TechnicalAnalyzer, prepare_data_for_ta_lib


class TestTechnicalAnalyzerUnit:
    """Pure-unit tests – no real HTTP traffic"""

    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer("dummy_av_key")

    # ---------- _map_interval ----------
    def test_map_interval_mapping(self, analyzer):
        """Test interval mapping to Alpha Vantage function names"""
        # Test intraday intervals
        func, interval = analyzer._map_interval("1min")
        assert func == "TIME_SERIES_INTRADAY"
        assert interval == "1min"
        
        func, interval = analyzer._map_interval("60min")
        assert func == "TIME_SERIES_INTRADAY" 
        assert interval == "60min"
        
        # Test daily/weekly/monthly
        func, interval = analyzer._map_interval("1D")
        assert func == "TIME_SERIES_DAILY"
        assert interval is None
        
        func, interval = analyzer._map_interval("1W")
        assert func == "TIME_SERIES_WEEKLY"
        assert interval is None

    def test_map_interval_invalid(self, analyzer):
        """Test invalid interval handling"""
        with pytest.raises(ValueError, match="Unsupported interval"):
            analyzer._map_interval("invalid")

    # ---------- _clean_historical_data ----------
    def test_clean_historical_data_filters_bad_rows(self, analyzer):
        raw = pd.DataFrame(
            {
                "symbol": ["AAPL", "AAPL", "AAPL"],
                "datetime": pd.to_datetime([
                    "2025-07-23T14:30:00Z",
                    "2025-07-24T14:30:00Z",
                    "2025-07-25T14:30:00Z",
                ]),
                "open": [200, 0, 205],      # second row invalid (open=0)
                "high": [210, 0, 208],
                "low": [198, 0, 204],
                "close": [205, 0, 207],
                "volume": [10_000, 20_000, -5],  # last row invalid (volume <0)
            }
        )
        cleaned = analyzer._clean_historical_data(raw)
        # Only first row should survive
        assert len(cleaned) == 1
        assert cleaned.iloc[0]["open"] == 200
        # derived columns exist
        assert {"price_change", "typical_price", "true_range"} <= set(cleaned.columns)

    # ---------- _add_basic_features ----------
    def test_add_basic_features_math(self, analyzer):
        df = pd.DataFrame(
            {
                "symbol": ["AAPL", "AAPL"],
                "datetime": pd.to_datetime(["2025-07-24", "2025-07-25"]),
                "open": [100, 110],
                "high": [110, 120],
                "low": [95, 105],
                "close": [108, 115],
                "volume": [1_000, 2_000],
            }
        )
        featured = analyzer._add_basic_features(df.copy())
        # price_change equals 7 on second row
        assert featured.loc[1, "price_change"] == pytest.approx(7)
        # price_change_pct equals 6.48 %
        assert featured.loc[1, "price_change_pct"] == pytest.approx(6.481, abs=1e-3)
        # typical_price = (H+L+C)/3
        assert featured.loc[1, "typical_price"] == pytest.approx((120 + 105 + 115) / 3)

    # ---------- get_historical_data (HTTP mocked) ----------
    def test_get_historical_data_happy_path(self, analyzer):
        # Mock Alpha Vantage response format
        mock_json = {
            "Time Series (60min)": {
                "2025-07-25 15:30:00": {
                    "1. open": "108.0000",
                    "2. high": "110.0000", 
                    "3. low": "107.0000",
                    "4. close": "109.5000",
                    "5. volume": "15000"
                },
                "2025-07-24 15:30:00": {
                    "1. open": "100.0000",
                    "2. high": "105.0000",
                    "3. low": "99.0000", 
                    "4. close": "102.0000",
                    "5. volume": "12345"
                }
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", json=mock_json)
            # Updated method signature - no period parameter
            df = analyzer.get_historical_data(["AAPL"], interval="60min", outputsize="compact")
            
        assert len(df) == 2
        assert all(df["symbol"] == "AAPL")
        # FIX 1: Data is sorted by datetime ascending, so earlier date comes first
        assert df.iloc[0]["close"] == 102.0  # 2025-07-24 (earlier date)
        assert df.iloc[1]["close"] == 109.5  # 2025-07-25 (later date)

    def test_get_historical_data_daily_format(self, analyzer):
        """Test daily data format (no volume in some responses)"""
        mock_json = {
            "Time Series (Daily)": {
                "2025-07-25": {
                    "1. open": "150.0000",
                    "2. high": "155.0000",
                    "3. low": "149.0000",
                    "4. close": "153.0000",
                    "5. volume": "25000000"
                }
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", json=mock_json)
            df = analyzer.get_historical_data(["MSFT"], interval="1D", outputsize="compact")
            
        assert len(df) == 1
        assert df.iloc[0]["symbol"] == "MSFT"
        assert df.iloc[0]["volume"] == 25000000

    def test_get_historical_data_api_error_message(self, analyzer):
        """Test Alpha Vantage API error message handling"""
        mock_json = {
            "Error Message": "Invalid API call. Please retry or visit the documentation for TIME_SERIES_INTRADAY."
        }
        
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", json=mock_json)
            df = analyzer.get_historical_data(["AAPL"], interval="60min")
            
        assert df.empty

    def test_get_historical_data_rate_limit_note(self, analyzer):
        """Test Alpha Vantage rate limit note handling"""
        mock_json = {
            "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."
        }
        
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", json=mock_json)
            df = analyzer.get_historical_data(["AAPL"], interval="60min")
            
        assert df.empty

    def test_get_historical_data_handles_http_error(self, analyzer):
        """Test HTTP error handling"""
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", status_code=500)
            df = analyzer.get_historical_data(["AAPL"], interval="60min")
            
        assert df.empty

    # ---------- _fetch_symbol ---------- 
    def test_fetch_symbol_intraday(self, analyzer):
        """Test individual symbol fetching for intraday data"""
        mock_json = {
            "Time Series (5min)": {
                "2025-07-25 16:00:00": {
                    "1. open": "100.0",
                    "2. high": "101.0",
                    "3. low": "99.5",
                    "4. close": "100.5", 
                    "5. volume": "5000"
                }
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", json=mock_json)
            df = analyzer._fetch_symbol("AAPL", "5min", "compact")
            
        assert len(df) == 1
        assert df.iloc[0]["open"] == 100.0
        assert df.iloc[0]["volume"] == 5000.0

    def test_fetch_symbol_weekly_no_volume(self, analyzer):
        """Test weekly data parsing (volume might be missing)"""
        mock_json = {
            "Weekly Time Series": {
                "2025-07-25": {
                    "1. open": "100.0",
                    "2. high": "105.0", 
                    "3. low": "98.0",
                    "4. close": "103.0"
                    # Note: no volume field
                }
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", json=mock_json)
            df = analyzer._fetch_symbol("AAPL", "1W", "compact")
            
        assert len(df) == 1
        assert df.iloc[0]["volume"] == 0.0  # Default when missing

    # ---------- validate_data_quality ----------
    def test_validate_data_quality_reports(self, analyzer):
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "datetime": pd.to_datetime(["2025-07-24"]),
                "open": [100],
                "high": [105],
                "low": [95],
                "close": [102],
                "volume": [1000],
                "price_change": [0],
                "price_change_pct": [0],
                "typical_price": [100.67],
                "true_range": [10],
            }
        )
        report = analyzer.validate_data_quality(df)
        assert report["status"] == "valid"
        assert report["records"] == 1  # Updated field name

    # ---------- get_latest_prices ----------
    def test_get_latest_prices(self, analyzer):
        """Test latest prices extraction"""
        mock_json = {
            "Time Series (Daily)": {
                "2025-07-25": {
                    "1. open": "150.0",
                    "2. high": "155.0",
                    "3. low": "149.0", 
                    "4. close": "153.0",
                    "5. volume": "1000000"
                },
                "2025-07-24": {
                    "1. open": "148.0",
                    "2. high": "152.0",
                    "3. low": "147.0",
                    "4. close": "151.0", 
                    "5. volume": "900000"
                }
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get("https://www.alphavantage.co/query", json=mock_json)
            latest = analyzer.get_latest_prices(["AAPL"])
            
        assert len(latest) == 1
        assert latest.iloc[0]["symbol"] == "AAPL"
        assert latest.iloc[0]["close"] == 153.0  # Most recent price

    # ---------- prepare_data_for_ta_lib ----------
    def test_prepare_data_for_ta_lib_output(self):
        df = pd.DataFrame(
            {
                "symbol": ["AAPL", "AAPL"],
                "datetime": pd.to_datetime(["2025-07-24", "2025-07-25"]),
                "open": [10, 11],
                "high": [12, 13],
                "low": [9, 10],
                "close": [11, 12],
                "volume": [100, 120],
                "price_change": [1, 1],
                "price_change_pct": [10, 9],
                "typical_price": [11, 11.67],
                "true_range": [3, 3],
            }
        )
        out = prepare_data_for_ta_lib(df)
        assert "AAPL" in out
        assert len(out["AAPL"]) == 2
        assert "date" in out["AAPL"].columns

    # ---------- constructor tests ----------
    def test_constructor_with_explicit_key(self):
        """Test constructor with explicit API key"""
        analyzer = TechnicalAnalyzer(av_api_key="test_key", request_pause=5.0)
        assert analyzer.api_key == "test_key"
        assert analyzer.request_pause == 5.0

    def test_constructor_missing_key_raises_error(self):
        """Test constructor raises error when no API key available"""
        # FIX 2: Use patch.dict to completely clear environment and patch load_dotenv
        with patch.dict(os.environ, {}, clear=True):
            with patch("technical_analyzer.load_dotenv", return_value=None):
                with pytest.raises(ValueError, match="ALPHAVANTAGE_API_KEY not found"):
                    TechnicalAnalyzer()

    @patch.dict('os.environ', {'ALPHAVANTAGE_API_KEY': 'env_test_key'})
    def test_constructor_loads_from_env(self):
        """Test constructor loads API key from environment"""
        analyzer = TechnicalAnalyzer()
        assert analyzer.api_key == "env_test_key"
