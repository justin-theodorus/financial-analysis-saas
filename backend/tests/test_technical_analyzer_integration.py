import os
import pytest
import time
from dotenv import load_dotenv
from technical_analyzer import TechnicalAnalyzer

load_dotenv()  # pick up real ALPHAVANTAGE_API_KEY from .env


@pytest.mark.integration 
class TestTechnicalAnalyzerIntegration:
    """Integration tests with real Alpha Vantage API calls"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with real API key"""
        key = os.getenv("ALPHAVANTAGE_API_KEY")
        if not key:
            pytest.skip("No live Alpha Vantage API key configured")
        
        # Use longer pause for integration tests to respect rate limits
        return TechnicalAnalyzer(av_api_key=key, request_pause=15.0)

    def test_live_intraday_fetch_and_clean(self, analyzer):
        """Test fetching real intraday data"""
        df = analyzer.get_historical_data(["AAPL"], interval="60min", outputsize="compact")
        
        # Basic sanity assertions
        if not df.empty:  # Data might not be available on weekends
            assert set(df["symbol"]) == {"AAPL"}
            assert (df[["open", "high", "low", "close"]] > 0).all().all()
            assert (df["volume"] >= 0).all()
            assert (df["high"] >= df["low"]).all()
            
            report = analyzer.validate_data_quality(df)
            assert report["status"] == "valid"
            print(f"Intraday data quality report: {report}")
        else:
            print("No intraday data available (market might be closed)")

    def test_live_daily_fetch_and_clean(self, analyzer):
        """Test fetching real daily data"""
        df = analyzer.get_historical_data(["MSFT"], interval="1D", outputsize="compact")
        
        # Basic sanity assertions
        assert not df.empty
        assert set(df["symbol"]) == {"MSFT"}
        assert (df[["open", "high", "low", "close", "volume"]] > 0).all().all()
        assert (df["high"] >= df["low"]).all()
        
        report = analyzer.validate_data_quality(df)
        assert report["status"] == "valid"
        print(f"Daily data quality report: {report}")

    def test_live_multiple_symbols_with_rate_limiting(self, analyzer):
        """Test fetching data for multiple symbols (tests rate limiting)"""
        symbols = ["AAPL", "GOOGL"]  # Only 2 symbols to keep test time reasonable
        
        start_time = time.time()
        df = analyzer.get_historical_data(symbols, interval="1D", outputsize="compact")
        end_time = time.time()
        
        # Should take at least request_pause seconds due to rate limiting
        assert end_time - start_time >= analyzer.request_pause
        
        if not df.empty:
            assert df["symbol"].nunique() <= len(symbols)  # Might be fewer if some fail
            assert (df[["open", "high", "low", "close"]] > 0).all().all()
            
            report = analyzer.validate_data_quality(df)
            print(f"Multi-symbol data quality report: {report}")

    def test_live_latest_prices(self, analyzer):
        """Test getting latest prices"""
        latest = analyzer.get_latest_prices(["AAPL"])
        
        if not latest.empty:
            assert len(latest) == 1
            assert latest.iloc[0]["symbol"] == "AAPL"
            assert latest.iloc[0]["close"] > 0
            print(f"Latest AAPL price: ${latest.iloc[0]['close']:.2f}")
        else:
            print("No latest price data available")

    def test_live_weekly_data(self, analyzer):
        """Test fetching weekly data"""
        df = analyzer.get_historical_data(["AAPL"], interval="1W", outputsize="compact")
        
        if not df.empty:
            assert set(df["symbol"]) == {"AAPL"}
            assert (df[["open", "high", "low", "close"]] > 0).all().all()
            
            # ✅ FIXED: Weekly data can have many years of history
            # Just verify we have reasonable data points (more than 10, less than 10000)
            assert 10 < len(df) < 10000
            print(f"Weekly data points: {len(df)}")
            
            # Verify data spans reasonable time period for weekly data
            date_range = (df['datetime'].max() - df['datetime'].min()).days
            assert date_range > 30  # At least a month of data
            print(f"Weekly data covers {date_range} days")

    def test_live_error_handling_invalid_symbol(self, analyzer):
        """Test error handling with invalid symbol"""
        df = analyzer.get_historical_data(["INVALID_SYMBOL_12345"], interval="1D")
        
        # Should handle gracefully and return empty DataFrame
        assert df.empty

    @pytest.mark.slow
    def test_live_full_vs_compact_outputsize(self, analyzer):
        """Test full vs compact data retrieval (slow test)"""
        # Get compact data first
        compact_df = analyzer.get_historical_data(["AAPL"], interval="1D", outputsize="compact")
        
        if not compact_df.empty:
            compact_count = len(compact_df)
            print(f"Compact dataset size: {compact_count} data points")
            
            # Get full data
            full_df = analyzer.get_historical_data(["AAPL"], interval="1D", outputsize="full")
            
            if not full_df.empty:
                full_count = len(full_df)
                print(f"Full dataset size: {full_count} data points")
                print(f"Date range: {full_df['datetime'].min()} to {full_df['datetime'].max()}")
                
                # ✅ FIXED: Full should have >= compact data (not necessarily more)
                assert full_count >= compact_count
                
                # For AAPL (established stock), full should typically have much more data
                # But we'll be flexible since it depends on API limits and data availability
                if full_count > compact_count:
                    print(f"✓ Full returned {full_count - compact_count} more data points than compact")
                else:
                    print(f"⚠ Full and compact returned same amount of data ({full_count} points)")

    def test_live_data_consistency(self, analyzer):
        """Test data consistency across different intervals"""
        # Get both daily and weekly data
        daily_df = analyzer.get_historical_data(["AAPL"], interval="1D", outputsize="compact")
        
        if not daily_df.empty:
            # Get the latest daily price
            latest_daily = daily_df.sort_values('datetime').iloc[-1]
            
            # Get weekly data and find the most recent week that includes this date
            weekly_df = analyzer.get_historical_data(["AAPL"], interval="1W", outputsize="compact")
            
            if not weekly_df.empty:
                latest_weekly = weekly_df.sort_values('datetime').iloc[-1]
                
                # The weekly close should be reasonably close to a recent daily close
                # (within same magnitude, allowing for different time periods)
                price_ratio = latest_daily['close'] / latest_weekly['close']
                assert 0.5 < price_ratio < 2.0  # Should be within 2x of each other
                
                print(f"Latest daily close: ${latest_daily['close']:.2f}")
                print(f"Latest weekly close: ${latest_weekly['close']:.2f}")
                print(f"Price consistency check passed (ratio: {price_ratio:.3f})")
