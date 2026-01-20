"""
CSV logger for decisions and trades.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class Logger:
    """CSV logger for bot decisions and trade executions."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.decisions_file = self.log_dir / "decisions.csv"
        self.trades_file = self.log_dir / "trades.csv"
        
        self._init_decisions_log()
        self._init_trades_log()
    
    def _init_decisions_log(self):
        """Initialize decisions CSV with headers if needed."""
        if not self.decisions_file.exists():
            with open(self.decisions_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'asset', 'slug', 'current_price', 
                    'price_to_beat', 'decision', 'seconds_left',
                    'ema9', 'ema20', 'atr', 'return_3m', 'return_5m',
                    'gap', 'gap_atr', 'reasoning', 'stake_usd', 'win_streak'
                ])
    
    def _init_trades_log(self):
        """Initialize trades CSV with headers if needed."""
        if not self.trades_file.exists():
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'asset', 'slug', 'decision', 
                    'stake_usd', 'win_streak_before', 'current_price',
                    'price_to_beat', 'seconds_left', 'executed',
                    'result', 'win_streak_after', 'note'
                ])
    
    def log_decision(self, data: Dict[str, Any]):
        """Log a trading decision to CSV.
        
        Args:
            data: Dictionary with decision details
        """
        with open(self.decisions_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get('timestamp', datetime.utcnow().isoformat()),
                data.get('asset'),
                data.get('slug'),
                data.get('current_price'),
                data.get('price_to_beat'),
                data.get('decision'),
                data.get('seconds_left'),
                data.get('ema9'),
                data.get('ema20'),
                data.get('atr'),
                data.get('return_3m'),
                data.get('return_5m'),
                data.get('gap'),
                data.get('gap_atr'),
                data.get('reasoning'),
                data.get('stake_usd'),
                data.get('win_streak')
            ])
        
        print(f"📝 Decision logged to {self.decisions_file}")
    
    def log_trade(self, data: Dict[str, Any]):
        """Log a trade execution to CSV.
        
        Args:
            data: Dictionary with trade details
        """
        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get('timestamp', datetime.utcnow().isoformat()),
                data.get('asset'),
                data.get('slug'),
                data.get('decision'),
                data.get('stake_usd'),
                data.get('win_streak_before'),
                data.get('current_price'),
                data.get('price_to_beat'),
                data.get('seconds_left'),
                data.get('executed', False),
                data.get('result'),
                data.get('win_streak_after'),
                data.get('note')
            ])
        
        print(f"📝 Trade logged to {self.trades_file}")
    
    def get_today_stats(self) -> Dict[str, int]:
        """Get today's trading statistics from logs.
        
        Returns:
            Dictionary with trades_count, wins, losses
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        stats = {"trades_count": 0, "wins": 0, "losses": 0}
        
        if not self.trades_file.exists():
            return stats
        
        with open(self.trades_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = row.get('timestamp', '')
                if timestamp.startswith(today):
                    if row.get('executed') == 'True':
                        stats['trades_count'] += 1
                        result = row.get('result', '').upper()
                        if result == 'W':
                            stats['wins'] += 1
                        elif result == 'L':
                            stats['losses'] += 1
        
        return stats
