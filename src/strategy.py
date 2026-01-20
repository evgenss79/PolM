"""
Trading strategy: decision engine for Up/Down selection.
"""

from typing import Dict, Any, Optional


class Strategy:
    """Decision engine for trading Up/Down based on technical analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Strategy configuration from config.json
        """
        self.gap_atr_threshold = config.get('gap_atr_threshold', 0.8)
        self.time_pressure_seconds = config.get('time_pressure_seconds', 600)
    
    def make_decision(
        self,
        current_price: float,
        price_to_beat: float,
        seconds_left: int,
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make Up/Down decision based on price, time, and indicators.
        
        Args:
            current_price: Current market price
            price_to_beat: Target price to beat
            seconds_left: Seconds until market close
            indicators: Technical indicators from TA module
        
        Returns:
            Dictionary with 'decision' ('UP' or 'DOWN') and 'reasoning'
        """
        # Extract indicators
        ema_fast = indicators.get('ema_fast')
        ema_slow = indicators.get('ema_slow')
        atr = indicators.get('atr')
        returns = indicators.get('returns', {})
        return_3m = returns.get('return_3m')
        return_5m = returns.get('return_5m')
        close = indicators.get('close', current_price)
        
        # Calculate gap
        gap = price_to_beat - current_price
        gap_atr = gap / atr if atr and atr > 0 else 0
        
        reasoning = []
        decision = None
        
        # Rule 1: Time pressure + large gap
        if seconds_left <= self.time_pressure_seconds and abs(gap_atr) > self.gap_atr_threshold:
            if gap > 0:  # Need price to go UP to beat
                decision = 'DOWN'
                reasoning.append(
                    f"⏰ Time pressure ({seconds_left}s left) + large gap (gap/ATR={gap_atr:.2f}) "
                    f"→ Price unlikely to rise ${gap:.2f} to beat target"
                )
            else:  # Need price to go DOWN to beat
                decision = 'UP'
                reasoning.append(
                    f"⏰ Time pressure ({seconds_left}s left) + large gap (gap/ATR={gap_atr:.2f}) "
                    f"→ Price unlikely to fall ${abs(gap):.2f} to beat target"
                )
        
        # Rule 2: Strong trend analysis (if no time pressure decision)
        if decision is None and all(v is not None for v in [ema_fast, ema_slow, return_3m]):
            # Downtrend + need to go UP
            if ema_fast < ema_slow and return_3m < 0 and close < ema_fast and gap > 0:
                decision = 'DOWN'
                reasoning.append(
                    f"📉 Strong downtrend (EMA{ema_fast:.2f} < EMA{ema_slow:.2f}, "
                    f"return_3m={return_3m:.2f}%, close < EMA) + need to rise ${gap:.2f} "
                    f"→ Unlikely, betting DOWN"
                )
            
            # Uptrend + need to go DOWN
            elif ema_fast > ema_slow and return_3m > 0 and close > ema_fast and gap < 0:
                decision = 'UP'
                reasoning.append(
                    f"📈 Strong uptrend (EMA{ema_fast:.2f} > EMA{ema_slow:.2f}, "
                    f"return_3m={return_3m:.2f}%, close > EMA) + need to fall ${abs(gap):.2f} "
                    f"→ Unlikely, betting UP"
                )
        
        # Rule 3: Default logic based on gap
        if decision is None:
            if current_price < price_to_beat:
                decision = 'DOWN'
                reasoning.append(
                    f"📊 Default: Current price ${current_price:.2f} < "
                    f"price to beat ${price_to_beat:.2f} → Betting DOWN (No won't beat)"
                )
            else:
                decision = 'UP'
                reasoning.append(
                    f"📊 Default: Current price ${current_price:.2f} >= "
                    f"price to beat ${price_to_beat:.2f} → Betting UP (Yes will beat)"
                )
        
        # Build result
        result = {
            'decision': decision,
            'reasoning': ' | '.join(reasoning),
            'gap': gap,
            'gap_atr': gap_atr,
            'ema_fast': ema_fast,
            'ema_slow': ema_slow,
            'atr': atr,
            'return_3m': return_3m,
            'return_5m': return_5m
        }
        
        # Print decision explanation
        print("\n" + "="*70)
        print("🎯 TRADING DECISION")
        print("="*70)
        print(f"Current Price: ${current_price:.2f}")
        print(f"Price to Beat: ${price_to_beat:.2f}")
        print(f"Gap: ${gap:+.2f}")
        print(f"Seconds Left: {seconds_left}s ({seconds_left//60}m {seconds_left%60}s)")
        
        if ema_fast and ema_slow:
            print(f"\nTechnical Indicators:")
            print(f"  EMA(9): ${ema_fast:.2f}")
            print(f"  EMA(20): ${ema_slow:.2f}")
        if atr:
            print(f"  ATR: ${atr:.2f}")
            print(f"  Gap/ATR: {gap_atr:.2f}")
        if return_3m is not None:
            print(f"  Return 3m: {return_3m:+.2f}%")
        if return_5m is not None:
            print(f"  Return 5m: {return_5m:+.2f}%")
        
        print(f"\n💡 Reasoning:")
        print(f"  {result['reasoning']}")
        
        print(f"\n✅ DECISION: {decision}")
        print("="*70 + "\n")
        
        return result
    
    def should_trade(
        self,
        seconds_left: int,
        min_seconds: int,
        max_seconds: int
    ) -> tuple[bool, str]:
        """Check if conditions are suitable for trading.
        
        Args:
            seconds_left: Seconds until market close
            min_seconds: Minimum seconds before close to trade
            max_seconds: Maximum seconds before close to trade
        
        Returns:
            Tuple of (should_trade, reason)
        """
        if seconds_left < min_seconds:
            return False, f"Too close to market close ({seconds_left}s < {min_seconds}s minimum)"
        
        if seconds_left > max_seconds:
            return False, f"Too far from market close ({seconds_left}s > {max_seconds}s maximum)"
        
        return True, "Time window is suitable for trading"
