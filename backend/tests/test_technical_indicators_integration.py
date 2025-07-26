import pytest
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

from technical_analyzer import TechnicalAnalyzer
from technical_indicators import TechnicalIndicators, format_analysis_report, Signal

load_dotenv()


@pytest.mark.integration
class TestTechnicalIndicatorsIntegration:
    """Integration tests with real data and TA-Lib calculations"""

    @pytest.fixture
    def tech_analyzer(self):
        """Create TechnicalAnalyzer with real API key"""
        key = os.getenv("ALPHAVANTAGE_API_KEY")
        if not key:
            pytest.skip("No live Alpha Vantage API key configured")
        return TechnicalAnalyzer(av_api_key=key, request_pause=15.0)

    @pytest.fixture
    def tech_indicators(self):
        """Create TechnicalIndicators instance"""
        return TechnicalIndicators(
            ema_period=10,  # Shorter periods for testing
            rsi_period=10,
            macd_fast=8,
            macd_slow=17,
            macd_signal=6
        )

    def test_real_single_symbol_analysis(self, tech_analyzer, tech_indicators):
        """Test complete analysis pipeline with real data for single symbol"""
        # Fetch real historical data
        historical_data = tech_analyzer.get_historical_data(
            symbols=['AAPL'], 
            interval='1D', 
            outputsize='compact'
        )
        
        if historical_data.empty:
            pytest.skip("No historical data available")
        
        # Perform technical analysis
        results = tech_indicators.analyze_portfolio(historical_data)
        
        # Verify results
        assert len(results) == 1
        assert 'AAPL' in results
        
        result = results['AAPL']
        assert result.symbol == 'AAPL'
        assert result.current_price > 0
        assert len(result.indicators) == 3  # EMA, MACD, RSI
        assert result.overall_signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        assert 0 <= result.overall_confidence <= 100
        
        print(f"AAPL Analysis Result:")
        print(f"Price: ${result.current_price:.2f}")
        print(f"Signal: {result.overall_signal.name}")
        print(f"Confidence: {result.overall_confidence:.1f}%")
        print(f"Recommendation: {result.recommendation}")

    def test_real_multiple_symbols_analysis(self, tech_analyzer, tech_indicators):
        """Test analysis with multiple real symbols"""
        symbols = ['AAPL', 'MSFT']
        
        # Fetch real historical data
        historical_data = tech_analyzer.get_historical_data(
            symbols=symbols, 
            interval='1D', 
            outputsize='compact'
        )
        
        if historical_data.empty:
            pytest.skip("No historical data available")
        
        # Perform technical analysis
        results = tech_indicators.analyze_portfolio(historical_data)
        
        # Verify results
        assert len(results) <= len(symbols)  # Some might fail
        
        for symbol, result in results.items():
            assert symbol in symbols
            assert result.current_price > 0
            assert len(result.indicators) == 3
            assert result.overall_signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
            
            # Check individual indicators
            indicator_names = [ind.name for ind in result.indicators]
            assert 'EMA' in indicator_names
            assert 'MACD' in indicator_names
            assert 'RSI' in indicator_names
            
            print(f"\n{symbol} Analysis:")
            for indicator in result.indicators:
                print(f"  {indicator.name}: {indicator.signal.name} - {indicator.description}")

    def test_real_report_generation(self, tech_analyzer, tech_indicators):
        """Test report generation with real data"""
        # Fetch real data
        historical_data = tech_analyzer.get_historical_data(
            symbols=['AAPL'], 
            interval='1D', 
            outputsize='compact'
        )
        
        if historical_data.empty:
            pytest.skip("No historical data available")
        
        # Analyze
        results = tech_indicators.analyze_portfolio(historical_data)
        
        # Generate report
        report = format_analysis_report(results)
        
        # Verify report content
        assert "TECHNICAL ANALYSIS REPORT" in report
        assert "AAPL" in report
        assert "$" in report  # Price should be formatted
        assert any(emoji in report for emoji in ["🟢", "🔴", "🟡"])  # Signal emojis
        
        print("\nGenerated Report:")
        print(report)

    def test_real_indicator_calculations_validity(self, tech_analyzer, tech_indicators):
        """Test that real TA-Lib calculations produce valid results"""
        # Get real data with sufficient history
        historical_data = tech_analyzer.get_historical_data(
            symbols=['AAPL'], 
            interval='1D', 
            outputsize='full'  # Get more data for better calculations
        )
        
        if historical_data.empty or len(historical_data) < 50:
            pytest.skip("Insufficient historical data for validation")
        
        # Test individual indicators with real data
        aapl_data = historical_data[historical_data['symbol'] == 'AAPL'].copy()
        aapl_data = aapl_data.sort_values('datetime').reset_index(drop=True)
        
        close_prices = aapl_data['close'].values.astype(np.float64)
        
        # Test EMA
        ema_values, ema_result = tech_indicators.calculate_ema(close_prices)
        assert len(ema_values) > 0
        assert not np.isnan(ema_result.value)
        assert ema_result.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        
        # Test MACD
        macd_data, macd_result = tech_indicators.calculate_macd(close_prices)
        assert len(macd_data) > 0
        assert 'macd' in macd_data
        assert not np.isnan(macd_result.value)
        assert macd_result.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        
        # Test RSI
        rsi_values, rsi_result = tech_indicators.calculate_rsi(close_prices)
        assert len(rsi_values) > 0
        assert 0 <= rsi_result.value <= 100  # RSI should be between 0-100
        assert rsi_result.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        
        print(f"\nIndicator Values for AAPL:")
        print(f"EMA: {ema_result.value:.2f} (Signal: {ema_result.signal.name})")
        print(f"MACD: {macd_result.value:.4f} (Signal: {macd_result.signal.name})")
        print(f"RSI: {rsi_result.value:.2f} (Signal: {rsi_result.signal.name})")

    def test_real_edge_cases(self, tech_analyzer, tech_indicators):
        """Test edge cases with real data"""
        # Test with limited data (should handle gracefully)
        limited_data = tech_analyzer.get_historical_data(
            symbols=['AAPL'], 
            interval='60min',  # Intraday data might be limited
            outputsize='compact'
        )
        
        if not limited_data.empty:
            results = tech_indicators.analyze_portfolio(limited_data)
            
            # Should either produce results or handle gracefully
            if results:
                for symbol, result in results.items():
                    # Basic validity checks
                    assert result.current_price > 0
                    assert isinstance(result.overall_confidence, (int, float))
                    assert 0 <= result.overall_confidence <= 100
            else:
                print("Analysis handled limited data gracefully by returning no results")

    def test_real_consistency_check(self, tech_analyzer, tech_indicators):
        """Test consistency of results across multiple runs"""
        # Fetch the same data twice
        historical_data1 = tech_analyzer.get_historical_data(
            symbols=['AAPL'], 
            interval='1D', 
            outputsize='compact'
        )
        
        if historical_data1.empty:
            pytest.skip("No historical data available")
        
        # Run analysis twice
        results1 = tech_indicators.analyze_portfolio(historical_data1)
        results2 = tech_indicators.analyze_portfolio(historical_data1)
        
        # Results should be identical for same data
        if results1 and results2 and 'AAPL' in results1 and 'AAPL' in results2:
            result1 = results1['AAPL']
            result2 = results2['AAPL']
            
            assert result1.overall_signal == result2.overall_signal
            assert abs(result1.overall_confidence - result2.overall_confidence) < 0.01
            assert result1.current_price == result2.current_price
            
            print("✓ Consistency check passed - identical results for same data")

    @pytest.mark.slow
    def test_real_performance_benchmark(self, tech_analyzer, tech_indicators):
        """Test performance with larger dataset"""
        import time
        
        # Fetch more symbols and data
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        start_time = time.time()
        historical_data = tech_analyzer.get_historical_data(
            symbols=symbols, 
            interval='1D', 
            outputsize='compact'
        )
        fetch_time = time.time() - start_time
        
        if historical_data.empty:
            pytest.skip("No historical data available")
        
        start_time = time.time()
        results = tech_indicators.analyze_portfolio(historical_data)
        analysis_time = time.time() - start_time
        
        print(f"\nPerformance Benchmark:")
        print(f"Data fetch time: {fetch_time:.2f}s")
        print(f"Analysis time: {analysis_time:.2f}s")
        print(f"Symbols analyzed: {len(results)}")
        print(f"Average time per symbol: {analysis_time / max(len(results), 1):.2f}s")
        
        # Performance should be reasonable
        assert analysis_time < 30  # Should complete within 30 seconds
        assert len(results) > 0
