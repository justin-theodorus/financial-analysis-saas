import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import the modules we're testing
from technical_indicators import (
    TechnicalIndicators, Signal, IndicatorResult, TechnicalAnalysisResult,
    format_analysis_report
)


class TestTechnicalIndicatorsUnit:
    """Unit tests for TechnicalIndicators - no real TA-Lib calls"""

    @pytest.fixture
    def indicators(self):
        """Create TechnicalIndicators instance with test parameters"""
        return TechnicalIndicators(
            ema_period=10,
            macd_fast=12,
            macd_slow=26,
            macd_signal=9,
            rsi_period=14,
            rsi_oversold=30.0,
            rsi_overbought=70.0
        )

    @pytest.fixture
    def sample_symbol_data(self):
        """Create sample symbol data for testing"""
        dates = pd.date_range(start='2025-01-01', periods=50, freq='D')
        prices = np.random.uniform(100, 200, 50)
        
        return pd.DataFrame({
            'symbol': ['AAPL'] * 50,
            'datetime': dates,
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 50)
        })

    # ---------- Constructor Tests ----------
    def test_constructor_default_parameters(self):
        """Test constructor with default parameters"""
        indicators = TechnicalIndicators()
        assert indicators.ema_period == 20
        assert indicators.macd_fast == 12
        assert indicators.macd_slow == 26
        assert indicators.macd_signal == 9
        assert indicators.rsi_period == 14
        assert indicators.rsi_oversold == 30.0
        assert indicators.rsi_overbought == 70.0

    def test_constructor_custom_parameters(self, indicators):
        """Test constructor with custom parameters"""
        assert indicators.ema_period == 10
        assert indicators.min_data_points == 26 + 9 + 10  # max of periods + buffer

    # ---------- EMA Tests ----------
    @patch('talib.EMA')  # ✅ FIXED: Direct patch
    def test_calculate_ema_buy_signal(self, mock_ema, indicators):
        """Test EMA calculation with buy signal"""
        close_prices = np.array([100.0, 105.0, 110.0, 115.0, 120.0] + [120.0] * 10)  # Ensure enough data
        mock_ema.return_value = np.array([np.nan] * 5 + [105.0, 108.0, 110.0, 112.0, 115.0] + [118.0] * 5)
        
        ema_values, result = indicators.calculate_ema(close_prices)
        
        mock_ema.assert_called_once_with(close_prices, timeperiod=10)
        assert result.signal == Signal.BUY
        assert result.name == "EMA"
        assert result.value == 118.0  # Last EMA value
        assert result.reference_value == 120.0  # Current price
        assert "above EMA" in result.description

    @patch('talib.EMA')  # ✅ FIXED: Direct patch
    def test_calculate_ema_sell_signal(self, mock_ema, indicators):
        """Test EMA calculation with sell signal"""
        close_prices = np.array([120.0, 115.0, 110.0, 105.0, 100.0] + [100.0] * 10)  # Ensure enough data
        mock_ema.return_value = np.array([np.nan] * 5 + [115.0, 112.0, 110.0, 108.0, 105.0] + [102.0] * 5)
        
        ema_values, result = indicators.calculate_ema(close_prices)
        
        mock_ema.assert_called_once_with(close_prices, timeperiod=10)
        assert result.signal == Signal.SELL  # ✅ FIXED: Should be SELL since price (100) < EMA (102)
        assert result.value == 102.0  # Last EMA value
        assert result.reference_value == 100.0  # Current price
        assert "below EMA" in result.description

    def test_calculate_ema_insufficient_data(self, indicators):
        """Test EMA with insufficient data"""
        close_prices = np.array([100, 105])  # Only 2 points, need 10
        
        ema_values, result = indicators.calculate_ema(close_prices)
        
        assert len(ema_values) == 0
        assert result.signal == Signal.HOLD
        assert "Insufficient data" in result.description

    # ---------- MACD Tests ----------
    @patch('talib.MACD')  # ✅ FIXED: Direct patch
    def test_calculate_macd_buy_signal(self, mock_macd, indicators):
        """Test MACD calculation with buy signal"""
        close_prices = np.array([100.0] * 40)  # Enough data for MACD
        mock_macd.return_value = (
            np.array([0.0] * 39 + [0.5]),      # MACD line
            np.array([0.0] * 39 + [0.3]),      # Signal line
            np.array([0.0] * 39 + [0.2])       # Histogram
        )
        
        macd_data, result = indicators.calculate_macd(close_prices)
        
        mock_macd.assert_called_once_with(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
        assert result.signal == Signal.BUY
        assert result.name == "MACD"
        assert result.value == 0.5  # Current MACD
        assert result.reference_value == 0.3  # Current signal
        assert "above Signal" in result.description

    @patch('talib.MACD')  # ✅ FIXED: Direct patch
    def test_calculate_macd_sell_signal(self, mock_macd, indicators):
        """Test MACD calculation with sell signal"""
        close_prices = np.array([100.0] * 40)
        mock_macd.return_value = (
            np.array([0.0] * 39 + [-0.5]),     # MACD line
            np.array([0.0] * 39 + [-0.3]),     # Signal line  
            np.array([0.0] * 39 + [-0.2])      # Histogram
        )
        
        macd_data, result = indicators.calculate_macd(close_prices)
        
        assert result.signal == Signal.SELL
        assert result.value == -0.5
        assert result.reference_value == -0.3
        assert "below Signal" in result.description

    def test_calculate_macd_insufficient_data(self, indicators):
        """Test MACD with insufficient data"""
        close_prices = np.array([100.0] * 20)  # Need at least 35 (26+9)
        
        macd_data, result = indicators.calculate_macd(close_prices)
        
        assert len(macd_data) == 0
        assert result.signal == Signal.HOLD
        assert "Insufficient data" in result.description

    # ---------- RSI Tests ----------
    @patch('talib.RSI')  # ✅ FIXED: Direct patch
    def test_calculate_rsi_buy_signal(self, mock_rsi, indicators):
        """Test RSI calculation with buy signal (oversold)"""
        close_prices = np.array([100.0] * 20)
        mock_rsi.return_value = np.array([50.0] * 19 + [25.0])  # RSI = 25 (oversold)
        
        rsi_values, result = indicators.calculate_rsi(close_prices)
        
        mock_rsi.assert_called_once_with(close_prices, timeperiod=14)
        assert result.signal == Signal.BUY
        assert result.name == "RSI"
        assert result.value == 25.0
        assert "oversold" in result.description

    @patch('talib.RSI')  # ✅ FIXED: Direct patch
    def test_calculate_rsi_sell_signal(self, mock_rsi, indicators):
        """Test RSI calculation with sell signal (overbought)"""
        close_prices = np.array([100.0] * 20)
        mock_rsi.return_value = np.array([50.0] * 19 + [75.0])  # RSI = 75 (overbought)
        
        rsi_values, result = indicators.calculate_rsi(close_prices)
        
        assert result.signal == Signal.SELL
        assert result.value == 75.0
        assert "overbought" in result.description

    @patch('talib.RSI')  # ✅ FIXED: Direct patch
    def test_calculate_rsi_hold_signal(self, mock_rsi, indicators):
        """Test RSI calculation with hold signal (neutral zone)"""
        close_prices = np.array([100.0] * 20)
        mock_rsi.return_value = np.array([50.0] * 20)  # RSI = 50 (neutral)
        
        rsi_values, result = indicators.calculate_rsi(close_prices)
        
        assert result.signal == Signal.HOLD
        assert result.value == 50.0
        assert "neutral zone" in result.description

    def test_calculate_rsi_insufficient_data(self, indicators):
        """Test RSI with insufficient data"""
        close_prices = np.array([100.0] * 10)  # Need at least 15 (14+1)
        
        rsi_values, result = indicators.calculate_rsi(close_prices)
        
        assert len(rsi_values) == 0
        assert result.signal == Signal.HOLD
        assert "Insufficient data" in result.description

    # ---------- Signal Combination Tests ----------
    def test_combine_signals_all_buy(self, indicators):
        """Test signal combination with all buy signals"""
        indicator_results = [
            IndicatorResult("EMA", Signal.BUY, 100, confidence=80),
            IndicatorResult("MACD", Signal.BUY, 0.5, confidence=70),
            IndicatorResult("RSI", Signal.BUY, 25, confidence=60)
        ]
        
        signal, confidence, recommendation = indicators._combine_signals(indicator_results)
        
        assert signal == Signal.BUY
        assert confidence > 0
        assert "3/3 indicators bullish" in recommendation

    def test_combine_signals_all_sell(self, indicators):
        """Test signal combination with all sell signals"""
        indicator_results = [
            IndicatorResult("EMA", Signal.SELL, 100, confidence=80),
            IndicatorResult("MACD", Signal.SELL, -0.5, confidence=70),
            IndicatorResult("RSI", Signal.SELL, 75, confidence=60)
        ]
        
        signal, confidence, recommendation = indicators._combine_signals(indicator_results)
        
        assert signal == Signal.SELL
        assert confidence > 0
        assert "3/3 indicators bearish" in recommendation

    def test_combine_signals_mixed(self, indicators):
        """Test signal combination with mixed signals"""
        indicator_results = [
            IndicatorResult("EMA", Signal.BUY, 100, confidence=80),
            IndicatorResult("MACD", Signal.SELL, -0.5, confidence=70),
            IndicatorResult("RSI", Signal.HOLD, 50, confidence=0)
        ]
        
        signal, confidence, recommendation = indicators._combine_signals(indicator_results)
        
        assert signal == Signal.HOLD
        assert "Mixed signals" in recommendation

    def test_combine_signals_all_hold(self, indicators):
        """Test signal combination with all hold signals"""
        indicator_results = [
            IndicatorResult("EMA", Signal.HOLD, 100, confidence=0),
            IndicatorResult("MACD", Signal.HOLD, 0, confidence=0),
            IndicatorResult("RSI", Signal.HOLD, 50, confidence=0)
        ]
        
        signal, confidence, recommendation = indicators._combine_signals(indicator_results)
        
        assert signal == Signal.HOLD
        assert confidence == 0.0
        assert "No clear signals" in recommendation

    def test_extreme_confidence_values(self, indicators):
        """Test confidence calculation with extreme values"""
        indicator_results = [
            IndicatorResult("EMA", Signal.BUY, 100, confidence=999),  # Very high
            IndicatorResult("MACD", Signal.BUY, 0.5, confidence=150)  # Above 100
        ]
        
        signal, confidence, recommendation = indicators._combine_signals(indicator_results)
        
        # Confidence should be capped at 100
        assert 0 <= confidence <= 100
        assert signal == Signal.BUY
        
        signal, confidence, recommendation = indicators._combine_signals(indicator_results)
        
        # Confidence should be reasonable, not extreme
        assert 0 <= confidence <= 100
