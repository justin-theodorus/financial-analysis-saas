import numpy as np
import pandas as pd
import talib
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from technical_analyzer import TechnicalAnalyzer, prepare_data_for_ta_lib


class Signal(Enum):
    """Trading signal enumeration"""
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class IndicatorResult:
    """Container for individual indicator results"""
    name: str
    signal: Signal
    value: float
    reference_value: Optional[float] = None
    confidence: float = 0.0
    description: str = ""


@dataclass
class TechnicalAnalysisResult:
    """Container for complete technical analysis results"""
    symbol: str
    datetime: pd.Timestamp
    current_price: float
    indicators: List[IndicatorResult]
    overall_signal: Signal
    overall_confidence: float
    recommendation: str


class TechnicalIndicators:
    """
    Technical Analysis using TA-Lib indicators
    
    Implements EMA, MACD, and RSI indicators with simple buy/sell logic
    """
    
    def __init__(self, 
                 ema_period: int = 20,
                 macd_fast: int = 12,
                 macd_slow: int = 26, 
                 macd_signal: int = 9,
                 rsi_period: int = 14,
                 rsi_oversold: float = 30.0,
                 rsi_overbought: float = 70.0):
        """
        Initialize technical indicators with parameters
        
        Args:
            ema_period (int): Period for Exponential Moving Average
            macd_fast (int): Fast period for MACD
            macd_slow (int): Slow period for MACD  
            macd_signal (int): Signal period for MACD
            rsi_period (int): Period for RSI calculation
            rsi_oversold (float): RSI oversold threshold
            rsi_overbought (float): RSI overbought threshold
        """
        self.ema_period = ema_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        
        # Minimum data points needed for calculations
        self.min_data_points = max(ema_period, macd_slow + macd_signal, rsi_period) + 10
    
    def calculate_ema(self, close_prices: np.ndarray) -> Tuple[np.ndarray, IndicatorResult]:
        """
        Calculate Exponential Moving Average and generate signal
        
        Args:
            close_prices (np.ndarray): Array of closing prices
            
        Returns:
            Tuple[np.ndarray, IndicatorResult]: EMA values and trading signal
        """
        if len(close_prices) < self.ema_period:
            return np.array([]), IndicatorResult(
                name="EMA",
                signal=Signal.HOLD,
                value=0.0,
                description=f"Insufficient data for EMA ({len(close_prices)} < {self.ema_period})"
            )
        
        # Calculate EMA using TA-Lib
        ema_values = talib.EMA(close_prices, timeperiod=self.ema_period)
        current_price = close_prices[-1]
        current_ema = ema_values[-1]
        
        # Simple EMA logic: Price above EMA = Buy, Price below EMA = Sell
        if current_price > current_ema:
            signal = Signal.BUY
            confidence = min((current_price - current_ema) / current_ema * 100, 100)
            description = f"Price (${current_price:.2f}) above EMA (${current_ema:.2f})"
        elif current_price < current_ema:
            signal = Signal.SELL
            confidence = min((current_ema - current_price) / current_ema * 100, 100)
            description = f"Price (${current_price:.2f}) below EMA (${current_ema:.2f})"
        else:
            signal = Signal.HOLD
            confidence = 0.0
            description = f"Price (${current_price:.2f}) at EMA (${current_ema:.2f})"
        
        return ema_values, IndicatorResult(
            name="EMA",
            signal=signal,
            value=current_ema,
            reference_value=current_price,
            confidence=confidence,
            description=description
        )
    
    def calculate_macd(self, close_prices: np.ndarray) -> Tuple[Dict[str, np.ndarray], IndicatorResult]:
        """
        Calculate MACD and generate signal
        
        Args:
            close_prices (np.ndarray): Array of closing prices
            
        Returns:
            Tuple[Dict[str, np.ndarray], IndicatorResult]: MACD values and trading signal
        """
        min_required = self.macd_slow + self.macd_signal
        if len(close_prices) < min_required:
            return {}, IndicatorResult(
                name="MACD",
                signal=Signal.HOLD,
                value=0.0,
                description=f"Insufficient data for MACD ({len(close_prices)} < {min_required})"
            )
        
        # Calculate MACD using TA-Lib
        macd_line, macd_signal_line, macd_histogram = talib.MACD(
            close_prices, 
            fastperiod=self.macd_fast,
            slowperiod=self.macd_slow,
            signalperiod=self.macd_signal
        )
        
        current_macd = macd_line[-1]
        current_signal = macd_signal_line[-1]
        current_histogram = macd_histogram[-1]
        
        # MACD logic: MACD above signal = Buy, MACD below signal = Sell
        # Also consider histogram for momentum
        if current_macd > current_signal and current_histogram > 0:
            signal = Signal.BUY
            confidence = min(abs(current_histogram) * 1000, 100)  # Scale histogram for confidence
            description = f"MACD ({current_macd:.4f}) above Signal ({current_signal:.4f})"
        elif current_macd < current_signal and current_histogram < 0:
            signal = Signal.SELL
            confidence = min(abs(current_histogram) * 1000, 100)
            description = f"MACD ({current_macd:.4f}) below Signal ({current_signal:.4f})"
        else:
            signal = Signal.HOLD
            confidence = 0.0
            description = f"MACD ({current_macd:.4f}) near Signal ({current_signal:.4f})"
        
        macd_data = {
            'macd': macd_line,
            'signal': macd_signal_line,
            'histogram': macd_histogram
        }
        
        return macd_data, IndicatorResult(
            name="MACD",
            signal=signal,
            value=current_macd,
            reference_value=current_signal,
            confidence=confidence,
            description=description
        )
    
    def calculate_rsi(self, close_prices: np.ndarray) -> Tuple[np.ndarray, IndicatorResult]:
        """
        Calculate RSI and generate signal
        
        Args:
            close_prices (np.ndarray): Array of closing prices
            
        Returns:
            Tuple[np.ndarray, IndicatorResult]: RSI values and trading signal
        """
        if len(close_prices) < self.rsi_period + 1:
            return np.array([]), IndicatorResult(
                name="RSI",
                signal=Signal.HOLD,
                value=0.0,
                description=f"Insufficient data for RSI ({len(close_prices)} < {self.rsi_period + 1})"
            )
        
        # Calculate RSI using TA-Lib
        rsi_values = talib.RSI(close_prices, timeperiod=self.rsi_period)
        current_rsi = rsi_values[-1]
        
        # RSI logic: RSI < 30 = Oversold (Buy), RSI > 70 = Overbought (Sell)
        if current_rsi < self.rsi_oversold:
            signal = Signal.BUY
            confidence = (self.rsi_oversold - current_rsi) / self.rsi_oversold * 100
            description = f"RSI ({current_rsi:.2f}) oversold (< {self.rsi_oversold})"
        elif current_rsi > self.rsi_overbought:
            signal = Signal.SELL
            confidence = (current_rsi - self.rsi_overbought) / (100 - self.rsi_overbought) * 100
            description = f"RSI ({current_rsi:.2f}) overbought (> {self.rsi_overbought})"
        else:
            signal = Signal.HOLD
            confidence = 0.0
            description = f"RSI ({current_rsi:.2f}) in neutral zone"
        
        return rsi_values, IndicatorResult(
            name="RSI",
            signal=signal,
            value=current_rsi,
            confidence=min(confidence, 100),
            description=description
        )
    
    def analyze_symbol(self, symbol_data: pd.DataFrame) -> Optional[TechnicalAnalysisResult]:
        """
        Perform complete technical analysis for a single symbol
        
        Args:
            symbol_data (pd.DataFrame): Historical data for one symbol
            
        Returns:
            Optional[TechnicalAnalysisResult]: Analysis results or None if insufficient data
        """
        if len(symbol_data) < self.min_data_points:
            print(f"⚠ Insufficient data for {symbol_data['symbol'].iloc[0]} "
                  f"({len(symbol_data)} < {self.min_data_points})")
            return None
        
        symbol = symbol_data['symbol'].iloc[0]
        
        # Prepare data for TA-Lib (requires numpy arrays)
        close_prices = symbol_data['close'].values.astype(np.float64)
        latest_datetime = symbol_data['datetime'].iloc[-1]
        current_price = close_prices[-1]
        
        # Calculate all indicators
        indicators = []
        
        # EMA
        ema_values, ema_result = self.calculate_ema(close_prices)
        indicators.append(ema_result)
        
        # MACD
        macd_data, macd_result = self.calculate_macd(close_prices)
        indicators.append(macd_result)
        
        # RSI
        rsi_values, rsi_result = self.calculate_rsi(close_prices)
        indicators.append(rsi_result)
        
        # Combine signals for overall recommendation
        overall_signal, overall_confidence, recommendation = self._combine_signals(indicators)
        
        return TechnicalAnalysisResult(
            symbol=symbol,
            datetime=latest_datetime,
            current_price=current_price,
            indicators=indicators,
            overall_signal=overall_signal,
            overall_confidence=overall_confidence,
            recommendation=recommendation
        )
    
    def _combine_signals(self, indicators: List[IndicatorResult]) -> Tuple[Signal, float, str]:
        """
        Combine individual indicator signals into overall recommendation
        """
        buy_signals = sum(1 for ind in indicators if ind.signal == Signal.BUY)
        sell_signals = sum(1 for ind in indicators if ind.signal == Signal.SELL)
        hold_signals = sum(1 for ind in indicators if ind.signal == Signal.HOLD)
        
        total_indicators = len(indicators)
        valid_signals = buy_signals + sell_signals
        
        if valid_signals == 0:
            return Signal.HOLD, 0.0, "No clear signals from indicators"
        
        # Calculate weighted confidence
        total_confidence = sum(ind.confidence for ind in indicators if ind.signal != Signal.HOLD)
        avg_confidence = total_confidence / valid_signals if valid_signals > 0 else 0.0
        
        # Determine overall signal
        if buy_signals > sell_signals:
            signal_strength = buy_signals / total_indicators
            overall_signal = Signal.BUY
            recommendation = f"BUY - {buy_signals}/{total_indicators} indicators bullish"
        elif sell_signals > buy_signals:
            signal_strength = sell_signals / total_indicators
            overall_signal = Signal.SELL
            recommendation = f"SELL - {sell_signals}/{total_indicators} indicators bearish"
        else:
            signal_strength = 0.5
            overall_signal = Signal.HOLD
            recommendation = f"HOLD - Mixed signals ({buy_signals} buy, {sell_signals} sell)"
        
        # Adjust confidence based on signal unanimity
        overall_confidence = avg_confidence * signal_strength
        
        # Cap confidence at 100
        overall_confidence = min(overall_confidence, 100.0)
        
        return overall_signal, overall_confidence, recommendation

    def analyze_portfolio(self, historical_data: pd.DataFrame) -> Dict[str, TechnicalAnalysisResult]:
        """
        Analyze multiple symbols from historical data
        
        Args:
            historical_data (pd.DataFrame): Combined historical data for multiple symbols
            
        Returns:
            Dict[str, TechnicalAnalysisResult]: Analysis results keyed by symbol
        """
        # Prepare data organized by symbol
        symbol_data = prepare_data_for_ta_lib(historical_data)
        results = {}
        
        print(f"Analyzing {len(symbol_data)} symbols with technical indicators...")
        
        for symbol, data in symbol_data.items():
            try:
                analysis = self.analyze_symbol(data)
                if analysis:
                    results[symbol] = analysis
                    print(f"✓ {symbol}: {analysis.overall_signal.name} "
                          f"(confidence: {analysis.overall_confidence:.1f}%)")
                else:
                    print(f"⚠ {symbol}: Insufficient data for analysis")
            except Exception as e:
                print(f"❌ {symbol}: Error in analysis - {e}")
        
        return results


def format_analysis_report(results: Dict[str, TechnicalAnalysisResult]) -> str:
    """
    Format technical analysis results into a readable report
    
    Args:
        results (Dict[str, TechnicalAnalysisResult]): Analysis results
        
    Returns:
        str: Formatted report
    """
    if not results:
        return "No analysis results to display."
    
    report = []
    report.append("=" * 80)
    report.append("TECHNICAL ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Analyzed {len(results)} symbols")
    report.append("")
    
    # Sort by overall confidence (descending)
    sorted_results = sorted(results.items(), 
                          key=lambda x: x[1].overall_confidence, 
                          reverse=True)
    
    for symbol, analysis in sorted_results:
        report.append(f"📊 {symbol} - ${analysis.current_price:.2f}")
        report.append(f"   Overall: {analysis.recommendation}")
        report.append(f"   Confidence: {analysis.overall_confidence:.1f}%")
        report.append(f"   Time: {analysis.datetime}")
        report.append("")
        
        # Individual indicators
        for indicator in analysis.indicators:
            signal_emoji = "🟢" if indicator.signal == Signal.BUY else "🔴" if indicator.signal == Signal.SELL else "🟡"
            report.append(f"   {signal_emoji} {indicator.name}: {indicator.description}")
        
        report.append("-" * 40)
    
    return "\n".join(report)


# Example usage and testing
if __name__ == "__main__":
    
    # Initialize components
    tech_analyzer = TechnicalAnalyzer()
    tech_indicators = TechnicalIndicators()
    
    # Fetch historical data with more data points for better analysis
    symbols = ['AAPL', 'MSFT']
    historical_data = tech_analyzer.get_historical_data(
        symbols=symbols, 
        interval='1D', 
        limit=100  # Get more data points for better technical analysis
    )
    
    if not historical_data.empty:
        # Perform technical analysis
        analysis_results = tech_indicators.analyze_portfolio(historical_data)
        
        # Display results
        report = format_analysis_report(analysis_results)
        print(report)
        
        # Access individual results programmatically
        for symbol, result in analysis_results.items():
            print(f"\n{symbol} Trading Decision:")
            print(f"Signal: {result.overall_signal.name}")
            print(f"Confidence: {result.overall_confidence:.1f}%")
            print(f"Recommendation: {result.recommendation}")
    else:
        print("No historical data retrieved for analysis.")
