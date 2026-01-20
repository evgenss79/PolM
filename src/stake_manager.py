"""
Stake manager with progressive doubling system.
"""

from typing import Dict, Any
from datetime import datetime
from .config import State


class StakeManager:
    """Manages progressive stake doubling and win/loss tracking."""
    
    def __init__(self, config: Dict[str, Any], state: State):
        """
        Args:
            config: Stake configuration from config.json
            state: State persistence object
        """
        self.base_stake = config.get('base_stake_usd', 2.0)
        self.max_stake = config.get('max_stake_usd', 1024.0)
        self.max_win_streak = config.get('max_win_streak', 15)
        self.reset_on_max_streak = config.get('reset_on_max_streak', True)
        self.result_mode = config.get('result_mode', 'manual')
        
        self.state = state
    
    def get_current_stake(self) -> float:
        """Get current stake amount.
        
        Returns:
            Current stake in USD
        """
        return self.state.get('current_stake', self.base_stake)
    
    def get_win_streak(self) -> int:
        """Get current win streak.
        
        Returns:
            Number of consecutive wins
        """
        return self.state.get('win_streak', 0)
    
    def can_trade(self, daily_stats: Dict[str, Any], safety_config: Dict[str, Any]) -> tuple[bool, str]:
        """Check if trading is allowed based on daily limits.
        
        Args:
            daily_stats: Daily statistics from state
            safety_config: Safety configuration
        
        Returns:
            Tuple of (can_trade, reason)
        """
        max_trades = safety_config.get('daily_max_trades', 10)
        max_loss = safety_config.get('daily_max_loss_usd', 20.0)
        
        trades_count = daily_stats.get('trades_count', 0)
        total_pnl = daily_stats.get('total_profit_loss', 0.0)
        
        if trades_count >= max_trades:
            return False, f"Daily trade limit reached ({trades_count}/{max_trades})"
        
        if total_pnl < -max_loss:
            return False, f"Daily loss limit exceeded (${total_pnl:.2f} < -${max_loss:.2f})"
        
        # Check if stake exceeds maximum
        current_stake = self.get_current_stake()
        if current_stake > self.max_stake:
            return False, f"Stake ${current_stake:.2f} exceeds maximum ${self.max_stake:.2f}"
        
        return True, "OK"
    
    def calculate_next_stake(self, result: str) -> float:
        """Calculate next stake based on result.
        
        Args:
            result: 'W' (win), 'L' (loss), or 'S' (skip)
        
        Returns:
            Next stake amount
        """
        current_stake = self.get_current_stake()
        win_streak = self.get_win_streak()
        
        result = result.upper()
        
        if result == 'W':
            # Win: double the stake
            new_streak = win_streak + 1
            
            # Check max streak
            if new_streak >= self.max_win_streak:
                if self.reset_on_max_streak:
                    print(f"🎊 Max win streak ({self.max_win_streak}) reached! Resetting to base stake.")
                    return self.base_stake
                else:
                    print(f"🎊 Max win streak ({self.max_win_streak}) reached! Pausing.")
                    return self.base_stake
            
            next_stake = current_stake * 2
            
            # Check max stake limit
            if next_stake > self.max_stake:
                print(f"⚠️  Doubling would exceed max stake (${next_stake:.2f} > ${self.max_stake:.2f})")
                print(f"   Capping at ${self.max_stake:.2f}")
                return self.max_stake
            
            return next_stake
        
        elif result == 'L':
            # Loss: reset to base stake
            return self.base_stake
        
        else:  # 'S' or unknown
            # Skip: no change
            return current_stake
    
    def update_after_result(self, result: str, stake_used: float) -> Dict[str, Any]:
        """Update state after trade result.
        
        Args:
            result: 'W' (win), 'L' (loss), or 'S' (skip)
            stake_used: Stake amount used in the trade
        
        Returns:
            Dictionary with updated values
        """
        result = result.upper()
        win_streak = self.get_win_streak()
        
        # Calculate next stake
        next_stake = self.calculate_next_stake(result)
        
        # Update streak
        if result == 'W':
            new_streak = min(win_streak + 1, self.max_win_streak)
        elif result == 'L':
            new_streak = 0
        else:  # Skip
            new_streak = win_streak
        
        # Calculate PNL (simplified: win = +stake, loss = -stake)
        pnl = stake_used if result == 'W' else (-stake_used if result == 'L' else 0)
        
        # Update state
        self.state.update(
            current_stake=next_stake,
            win_streak=new_streak,
            last_result=result,
            last_timestamp=datetime.utcnow().isoformat()
        )
        
        # Update daily stats
        daily_stats = self.state.get('daily_stats', {})
        daily_stats['trades_count'] = daily_stats.get('trades_count', 0) + (1 if result != 'S' else 0)
        daily_stats['wins'] = daily_stats.get('wins', 0) + (1 if result == 'W' else 0)
        daily_stats['losses'] = daily_stats.get('losses', 0) + (1 if result == 'L' else 0)
        daily_stats['total_profit_loss'] = daily_stats.get('total_profit_loss', 0) + pnl
        
        self.state.set('daily_stats', daily_stats)
        
        # Print update
        print("\n" + "="*70)
        print("💰 STAKE UPDATE")
        print("="*70)
        print(f"Result: {result} ({'WIN' if result == 'W' else 'LOSS' if result == 'L' else 'SKIP'})")
        print(f"Stake Used: ${stake_used:.2f}")
        print(f"PNL: ${pnl:+.2f}")
        print(f"Win Streak: {win_streak} → {new_streak}")
        print(f"Next Stake: ${next_stake:.2f}")
        print(f"\nDaily Stats:")
        print(f"  Trades: {daily_stats['trades_count']}")
        print(f"  W/L: {daily_stats['wins']}/{daily_stats['losses']}")
        print(f"  Total PNL: ${daily_stats['total_profit_loss']:+.2f}")
        print("="*70 + "\n")
        
        return {
            'next_stake': next_stake,
            'new_streak': new_streak,
            'pnl': pnl
        }
    
    def print_stake_info(self):
        """Print current stake information."""
        current_stake = self.get_current_stake()
        win_streak = self.get_win_streak()
        
        print("\n" + "="*70)
        print("💰 STAKE INFORMATION")
        print("="*70)
        print(f"Current Stake: ${current_stake:.2f}")
        print(f"Win Streak: {win_streak}/{self.max_win_streak}")
        print(f"Base Stake: ${self.base_stake:.2f}")
        print(f"Max Stake: ${self.max_stake:.2f}")
        print(f"\nProjection:")
        print(f"  If WIN:  Stake → ${self.calculate_next_stake('W'):.2f}, Streak → {min(win_streak + 1, self.max_win_streak)}")
        print(f"  If LOSS: Stake → ${self.calculate_next_stake('L'):.2f}, Streak → 0")
        print("="*70 + "\n")
    
    def ask_for_result(self) -> str:
        """Ask user for trade result (manual mode).
        
        Returns:
            'W', 'L', or 'S'
        """
        print("\n" + "="*70)
        print("📊 TRADE RESULT")
        print("="*70)
        print("Please enter the result of your trade:")
        print("  W = Win (price beat target)")
        print("  L = Loss (price did not beat target)")
        print("  S = Skip (unknown or cancelled)")
        print("="*70)
        
        while True:
            result = input("Result (W/L/S): ").strip().upper()
            if result in ['W', 'L', 'S']:
                return result
            print("❌ Invalid input. Please enter W, L, or S.")
