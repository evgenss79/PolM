"""
Technical analysis indicators: EMA, ATR, returns.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class TechnicalAnalysis:
    """Calculate technical indicators on candle data."""
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average.
        
        Args:
            df: DataFrame with OHLC data
            period: EMA period
            column: Column to calculate EMA on
        
        Returns:
            Series with EMA values
        """
        return df[column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range.
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period
        
        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        # True Range is max of the three
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR is EMA of True Range
        atr = tr.ewm(span=period, adjust=False).mean()
        
        return atr
    
    @staticmethod
    def calculate_percent_return(df: pd.DataFrame, periods: int, column: str = 'close') -> pd.Series:
        """Calculate percentage return over N periods.
        
        Args:
            df: DataFrame with price data
            periods: Number of periods to look back
            column: Column to calculate return on
        
        Returns:
            Series with percent returns
        """
        return df[column].pct_change(periods) * 100
    
    @staticmethod
    def get_indicators(
        df: pd.DataFrame,
        ema_fast: int = 9,
        ema_slow: int = 20,
        atr_period: int = 14,
        return_periods: list = [3, 5]
    ) -> Dict[str, Any]:
        """Calculate all indicators and return latest values.
        
        Args:
            df: DataFrame with OHLC data
            ema_fast: Fast EMA period
            ema_slow: Slow EMA period
            atr_period: ATR period
            return_periods: List of periods for return calculation
        
        Returns:
            Dictionary with latest indicator values
        """
        if len(df) == 0:
            return {
                'ema_fast': None,
                'ema_slow': None,
                'atr': None,
                'returns': {}
            }
        
        # Calculate EMAs
        ema_fast_series = TechnicalAnalysis.calculate_ema(df, ema_fast)
        ema_slow_series = TechnicalAnalysis.calculate_ema(df, ema_slow)
        
        # Calculate ATR
        atr_series = TechnicalAnalysis.calculate_atr(df, atr_period)
        
        # Calculate returns for different periods
        returns = {}
        for period in return_periods:
            ret_series = TechnicalAnalysis.calculate_percent_return(df, period)
            returns[f'return_{period}m'] = ret_series.iloc[-1] if len(ret_series) > 0 else None
        
        # Get latest values
        result = {
            'ema_fast': ema_fast_series.iloc[-1] if len(ema_fast_series) > 0 else None,
            'ema_slow': ema_slow_series.iloc[-1] if len(ema_slow_series) > 0 else None,
            'atr': atr_series.iloc[-1] if len(atr_series) > 0 else None,
            'returns': returns,
            'close': df['close'].iloc[-1] if len(df) > 0 else None
        }
        
        return result
    
    @staticmethod
    def detect_trend(ema_fast: float, ema_slow: float, close: float, return_3m: float) -> str:
        """Detect trend direction based on EMAs and recent return.
        
        Args:
            ema_fast: Fast EMA value
            ema_slow: Slow EMA value
            close: Current close price
            return_3m: 3-minute return percentage
        
        Returns:
            'uptrend', 'downtrend', or 'neutral'
        """
        if ema_fast is None or ema_slow is None or close is None or return_3m is None:
            return 'neutral'
        
        # Strong uptrend criteria
        if ema_fast > ema_slow and return_3m > 0 and close > ema_fast:
            return 'uptrend'
        
        # Strong downtrend criteria
        if ema_fast < ema_slow and return_3m < 0 and close < ema_fast:
            return 'downtrend'
        
        return 'neutral'
