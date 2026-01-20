"""
Configuration loader for Polymarket One-Click Bot.
Reads and validates config.json and state.json.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for the bot."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            # Copy example config if config doesn't exist
            example_path = f"{self.config_path}.example"
            if os.path.exists(example_path):
                print(f"📋 Creating config.json from {example_path}")
                with open(example_path, 'r') as f:
                    content = f.read()
                with open(self.config_path, 'w') as f:
                    f.write(content)
            else:
                raise FileNotFoundError(
                    f"Config file not found: {self.config_path}\n"
                    f"Please create it from config.json.example"
                )
        
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        self._validate()
        print(f"✅ Configuration loaded from {self.config_path}")
    
    def _validate(self):
        """Validate configuration values."""
        required_sections = ['assets', 'stake', 'safety', 'trading', 
                           'technical_analysis', 'strategy', 'browser', 
                           'api', 'logging']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate stake settings
        if self.config['stake']['base_stake_usd'] <= 0:
            raise ValueError("base_stake_usd must be positive")
        
        if self.config['stake']['max_win_streak'] > 15:
            print("⚠️  Warning: max_win_streak > 15 is not recommended")
        
        # Validate safety settings
        if not self.config['safety']['require_manual_confirmation']:
            raise ValueError(
                "require_manual_confirmation must be true for safety!\n"
                "This bot requires manual confirmation before trades."
            )
    
    def get(self, *keys, default=None):
        """Get nested configuration value.
        
        Args:
            *keys: Path to config value (e.g., 'stake', 'base_stake_usd')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_asset_config(self, asset: str) -> Dict[str, Any]:
        """Get configuration for specific asset (btc or eth)."""
        asset = asset.lower()
        if asset not in self.config['assets']:
            raise ValueError(f"Unknown asset: {asset}")
        return self.config['assets'][asset]


class State:
    """Stake manager state persistence."""
    
    def __init__(self, state_path: str = "state.json"):
        self.state_path = state_path
        self.state: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load state from JSON file."""
        if not os.path.exists(self.state_path):
            # Create from example or initialize defaults
            example_path = f"{self.state_path}.example"
            if os.path.exists(example_path):
                print(f"📋 Creating state.json from {example_path}")
                with open(example_path, 'r') as f:
                    content = f.read()
                with open(self.state_path, 'w') as f:
                    f.write(content)
            else:
                # Initialize with defaults
                self.state = {
                    "current_stake": 2.0,
                    "win_streak": 0,
                    "last_asset": None,
                    "last_slug": None,
                    "last_decision": None,
                    "last_timestamp": None,
                    "last_trade_id": None,
                    "last_result": None,
                    "daily_stats": {
                        "date": None,
                        "trades_count": 0,
                        "wins": 0,
                        "losses": 0,
                        "total_profit_loss": 0.0
                    }
                }
                self.save()
                return
        
        with open(self.state_path, 'r') as f:
            self.state = json.load(f)
        print(f"✅ State loaded: stake=${self.state['current_stake']}, streak={self.state['win_streak']}")
    
    def save(self):
        """Save state to JSON file atomically."""
        # Write to temp file first, then rename (atomic operation)
        temp_path = f"{self.state_path}.tmp"
        with open(temp_path, 'w') as f:
            json.dump(self.state, f, indent=2)
        os.replace(temp_path, self.state_path)
    
    def get(self, key: str, default=None):
        """Get state value."""
        return self.state.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set state value and save."""
        self.state[key] = value
        self.save()
    
    def update(self, **kwargs):
        """Update multiple state values and save once."""
        self.state.update(kwargs)
        self.save()
    
    def reset_daily_if_needed(self):
        """Reset daily stats if date changed."""
        from datetime import datetime
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        if self.state['daily_stats']['date'] != today:
            print(f"📅 New trading day: {today}")
            self.state['daily_stats'] = {
                "date": today,
                "trades_count": 0,
                "wins": 0,
                "losses": 0,
                "total_profit_loss": 0.0
            }
            self.save()
