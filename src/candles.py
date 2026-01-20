"""
Candle builder for creating 1-minute OHLC candles from price ticks.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd


class Candle:
    """Represents a single OHLC candle."""
    
    def __init__(self, timestamp: datetime):
        self.timestamp = timestamp
        self.open: Optional[float] = None
        self.high: Optional[float] = None
        self.low: Optional[float] = None
        self.close: Optional[float] = None
        self.volume: int = 0  # Number of ticks
    
    def update(self, price: float):
        """Update candle with new price tick."""
        if self.open is None:
            self.open = price
        
        if self.high is None or price > self.high:
            self.high = price
        
        if self.low is None or price < self.low:
            self.low = price
        
        self.close = price
        self.volume += 1
    
    def is_complete(self) -> bool:
        """Check if candle has all OHLC values."""
        return all(v is not None for v in [self.open, self.high, self.low, self.close])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert candle to dictionary."""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }


class CandleBuilder:
    """Builds 1-minute candles from price ticks."""
    
    def __init__(self, interval_seconds: int = 60, max_candles: int = 1000):
        """
        Args:
            interval_seconds: Candle interval in seconds (default 60 for 1-min)
            max_candles: Maximum number of candles to keep in memory
        """
        self.interval_seconds = interval_seconds
        self.max_candles = max_candles
        self.candles: List[Candle] = []
        self.current_candle: Optional[Candle] = None
    
    def add_tick(self, price: float, timestamp: datetime):
        """Add a price tick and update candles.
        
        Args:
            price: Current price
            timestamp: Tick timestamp
        """
        # Round timestamp to candle interval
        candle_time = self._round_to_interval(timestamp)
        
        # Create new candle if needed
        if self.current_candle is None or self.current_candle.timestamp != candle_time:
            # Save current candle if complete
            if self.current_candle and self.current_candle.is_complete():
                self.candles.append(self.current_candle)
                
                # Trim old candles if exceeded max
                if len(self.candles) > self.max_candles:
                    self.candles = self.candles[-self.max_candles:]
            
            # Start new candle
            self.current_candle = Candle(candle_time)
        
        # Update current candle with tick
        self.current_candle.update(price)
    
    def _round_to_interval(self, timestamp: datetime) -> datetime:
        """Round timestamp down to candle interval boundary.
        
        Args:
            timestamp: Input timestamp
        
        Returns:
            Rounded timestamp
        """
        epoch = datetime(1970, 1, 1, tzinfo=timestamp.tzinfo)
        seconds_since_epoch = (timestamp - epoch).total_seconds()
        rounded_seconds = int(seconds_since_epoch // self.interval_seconds) * self.interval_seconds
        return epoch + timedelta(seconds=rounded_seconds)
    
    def get_candles(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get completed candles.
        
        Args:
            count: Number of most recent candles to return (None = all)
        
        Returns:
            List of candle dictionaries
        """
        candles_data = [c.to_dict() for c in self.candles if c.is_complete()]
        
        if count:
            candles_data = candles_data[-count:]
        
        return candles_data
    
    def get_latest_price(self) -> Optional[float]:
        """Get most recent price (from current candle or last completed).
        
        Returns:
            Latest close price or None
        """
        if self.current_candle and self.current_candle.close is not None:
            return self.current_candle.close
        
        if self.candles and self.candles[-1].close is not None:
            return self.candles[-1].close
        
        return None
    
    def get_dataframe(self, count: Optional[int] = None) -> pd.DataFrame:
        """Get candles as pandas DataFrame.
        
        Args:
            count: Number of most recent candles to return (None = all)
        
        Returns:
            DataFrame with OHLC data
        """
        candles_data = self.get_candles(count)
        
        if not candles_data:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df = pd.DataFrame(candles_data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def has_enough_data(self, min_candles: int) -> bool:
        """Check if we have enough completed candles for analysis.
        
        Args:
            min_candles: Minimum required candles
        
        Returns:
            True if enough data available
        """
        return len(self.candles) >= min_candles
