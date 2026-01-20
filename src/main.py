"""
Main entry point for Polymarket One-Click Bot.

Usage:
    python src/main.py --asset btc
    python src/main.py --asset eth
    python src/main.py --asset btc --watch
"""

import argparse
import sys
import time
import signal
from datetime import datetime
from typing import Optional

# Import all modules
from .config import Config, State
from .logger import Logger
from .gamma import GammaAPI
from .rtds import RTDSClient
from .candles import CandleBuilder
from .ta import TechnicalAnalysis
from .strategy import Strategy
from .stake_manager import StakeManager
from .ui_oneclick import OneClickUI


class PolymrketBot:
    """Main orchestrator for Polymarket One-Click Bot."""
    
    def __init__(self, asset: str, watch_mode: bool = False):
        """
        Args:
            asset: Asset to trade ('btc' or 'eth')
            watch_mode: Enable watch mode for auto slug updates
        """
        self.asset = asset.lower()
        self.watch_mode = watch_mode
        self.running = True
        
        # Load configuration
        print("🚀 Polymarket One-Click Bot")
        print("="*70)
        
        self.config = Config()
        self.state = State()
        self.logger = Logger(self.config.get('logging', 'log_dir'))
        
        # Get asset configuration
        self.asset_config = self.config.get_asset_config(self.asset)
        
        # Initialize components
        self.gamma = GammaAPI(self.config.get('api', 'gamma_api_url'))
        
        symbol = self.asset_config['symbol']
        self.rtds = RTDSClient(
            self.config.get('api', 'rtds_websocket_url'),
            symbol
        )
        
        self.candles = CandleBuilder(
            interval_seconds=self.config.get('technical_analysis', 'candle_interval_seconds'),
            max_candles=self.config.get('technical_analysis', 'max_candles')
        )
        
        self.strategy = Strategy(self.config.get('strategy'))
        self.stake_manager = StakeManager(self.config.get('stake'), self.state)
        
        self.ui = OneClickUI(self.config.get('browser'), asset=self.asset)
        
        # Track current market
        self.current_slug: Optional[str] = None
        self.current_market_url: Optional[str] = None
        self.current_market_details: Optional[Dict[str, Any]] = None  # Gamma market details with token IDs
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n\n⚠️  Shutdown signal received...")
        self.running = False
    
    def run(self):
        """Main bot execution loop."""
        try:
            # Reset daily stats if needed
            self.state.reset_daily_if_needed()
            
            # Find active market (may start browser if needed for UI fallback)
            if not self._discover_market():
                print("❌ Could not find active market. Exiting.")
                return
            
            # Start browser if not already started (e.g., if events API succeeded)
            if not self.ui.browser and not self.ui.context:
                print("\n🌐 Starting browser for trading...")
                self.ui.start_browser()
            
            # Start price feed
            print(f"\n📡 Starting price feed for {self.asset_config['display_name']}...")
            self.rtds.start()
            
            # Wait for initial price data
            print("⏳ Collecting initial price data (60 seconds)...")
            self._collect_initial_data(duration=60)
            
            if not self.candles.has_enough_data(20):
                print("⚠️  Not enough price data collected. Continuing anyway...")
            
            # Navigate to market (browser already started by discovery or above)
            self.ui.navigate_to_market(self.current_market_url)
            
            # Check login status
            if not self.ui.check_if_logged_in():
                self.ui.prompt_login()
            
            # Main trading loop
            while self.running:
                try:
                    # Watch mode: check for new market
                    if self.watch_mode:
                        self._check_for_new_market()
                    
                    # Execute one trading cycle
                    self._trading_cycle()
                    
                    # If not watch mode, exit after one cycle
                    if not self.watch_mode:
                        break
                    
                    # Wait before next cycle
                    print(f"\n⏳ Waiting {self.config.get('trading', 'watch_interval_seconds')}s before next cycle...")
                    time.sleep(self.config.get('trading', 'watch_interval_seconds'))
                
                except KeyboardInterrupt:
                    print("\n⚠️  Interrupted by user")
                    break
                except Exception as e:
                    print(f"\n❌ Error in trading cycle: {e}")
                    if not self.watch_mode:
                        break
                    time.sleep(10)
        
        finally:
            self._cleanup()
    
    def _discover_market(self) -> bool:
        """Discover active 15m crypto market using two-level discovery.
        
        First attempts official /events API (reliable LIVE NOW filtering). If that fails,
        falls back to UI scraping (requires browser).
        
        Returns:
            True if market found, False otherwise
        """
        print(f"\n🔍 Discovering active {self.asset_config['display_name']} market...")
        
        slug_prefix = self.asset_config['slug_prefix']
        
        # Try /events API first (Primary) - no browser needed
        market_info = self.gamma.discover_15m_market(
            asset=self.asset,
            slug_prefix=slug_prefix,
            page=None,  # No browser for events API
            base_url=self.config.get('api', 'polymarket_base_url')
        )
        
        # If events API succeeded, we're done
        if market_info:
            self.current_slug = market_info['slug']
            self.current_market_url = market_info['url']
            
            print(f"✅ Market discovered!")
            print(f"   URL: {self.current_market_url}")
            print(f"   Source: {market_info.get('source', 'UNKNOWN')}")
            
            # Fetch market details with token IDs from Gamma API (official anchoring)
            print("\n📌 Anchoring market with official Gamma API data...")
            self.current_market_details = self.gamma.get_market_details_with_tokens(slug=self.current_slug)
            
            if not self.current_market_details:
                print("⚠️  Warning: Could not fetch market details with token IDs")
                print("   Trading will continue but without token ID verification")
            
            return True
        
        # Events API failed - try UI fallback (requires browser)
        print("\n🌐 Starting browser for UI fallback...")
        self.ui.start_browser()
        
        # Try discovery again with browser page
        market_info = self.gamma.discover_15m_market(
            asset=self.asset,
            slug_prefix=slug_prefix,
            page=self.ui.page,
            base_url=self.config.get('api', 'polymarket_base_url')
        )
        
        if not market_info:
            return False
        
        self.current_slug = market_info['slug']
        self.current_market_url = market_info['url']
        
        print(f"✅ Market discovered!")
        print(f"   URL: {self.current_market_url}")
        print(f"   Source: {market_info.get('source', 'UNKNOWN')}")
        
        # Fetch market details with token IDs from Gamma API (official anchoring)
        print("\n📌 Anchoring market with official Gamma API data...")
        self.current_market_details = self.gamma.get_market_details_with_tokens(slug=self.current_slug)
        
        if not self.current_market_details:
            print("⚠️  Warning: Could not fetch market details with token IDs")
            print("   Trading will continue but without token ID verification")
        
        return True
    
    def _check_for_new_market(self):
        """Check for new market in watch mode using two-level discovery."""
        if not self.watch_mode:
            return
        
        slug_prefix = self.asset_config['slug_prefix']
        
        # Use enhanced discovery - try Gamma API first
        market_info = self.gamma.discover_15m_market(
            asset=self.asset,
            slug_prefix=slug_prefix,
            page=self.ui.page,  # Browser is already running in watch mode
            base_url=self.config.get('api', 'polymarket_base_url')
        )
        
        # Check if it's a different market than current
        if market_info and market_info['slug'] != self.current_slug:
            print(f"\n🆕 New market detected!")
            print(f"   Old: {self.current_slug}")
            print(f"   New: {market_info['slug']}")
            print(f"   Source: {market_info.get('source', 'UNKNOWN')}")
            
            self.current_slug = market_info['slug']
            self.current_market_url = market_info['url']
            
            # Navigate to new market
            self.ui.navigate_to_market(self.current_market_url)
    
    def _collect_initial_data(self, duration: int):
        """Collect initial price data for technical analysis.
        
        Args:
            duration: Seconds to collect data
        """
        start_time = time.time()
        tick_count = 0
        
        while time.time() - start_time < duration and self.running:
            # Get all pending ticks
            ticks = self.rtds.get_all_prices()
            
            for tick in ticks:
                self.candles.add_tick(tick['price'], tick['timestamp'])
                tick_count += 1
            
            if tick_count > 0 and tick_count % 10 == 0:
                latest = self.candles.get_latest_price()
                if latest:
                    print(f"  📊 {tick_count} ticks collected, latest: ${latest:.2f}")
            
            time.sleep(1)
        
        print(f"✅ Collected {tick_count} price ticks")
        print(f"✅ Built {len(self.candles.get_candles())} complete 1-minute candles")
    
    def _trading_cycle(self):
        """Execute one complete trading cycle."""
        print("\n" + "="*70)
        print(f"🎯 TRADING CYCLE - {self.asset_config['display_name'].upper()}")
        print("="*70)
        
        # Continue collecting price data
        self._update_candles()
        
        # Parse market info from page
        price_to_beat, seconds_left = self.ui.parse_market_info()
        
        # Fallback to manual input if parsing failed
        if price_to_beat is None or seconds_left is None:
            price_to_beat, seconds_left = self.ui.ask_manual_market_info()
        
        # Get current price from candles (RTDS Chainlink)
        current_price = self.candles.get_latest_price()
        
        if current_price is None:
            print("❌ No current price available from RTDS.")
            print("   DIAGNOSTIC MODE: RTDS price feed has 0 ticks.")
            print("   This could mean:")
            print("   - WebSocket connection failed")
            print("   - No price updates received")
            print("   - Symbol mismatch in subscription")
            print("\n   ⚠️  Cannot continue trading cycle without RTDS price.")
            print("   Aborting this cycle.")
            return
        
        # RTDS vs price_to_beat cross-validation
        # Per task: RTDS current price and price_to_beat should be same order of magnitude
        print("\n🔍 Cross-validating RTDS price vs price_to_beat...")
        
        # Calculate order of magnitude difference
        price_ratio = current_price / price_to_beat if price_to_beat > 0 else 0
        
        # They should be within reasonable range (e.g., 0.5x to 2x)
        # If price_to_beat is way off (e.g., 0.21 vs 43000), ratio will be tiny
        if price_ratio < 0.5 or price_ratio > 2.0:
            print(f"❌ VALIDATION WARNING: RTDS price and price_to_beat are NOT same order of magnitude")
            print(f"   RTDS current price: ${current_price:.2f}")
            print(f"   Price to beat: ${price_to_beat:.2f}")
            print(f"   Ratio: {price_ratio:.4f}")
            print(f"\n   This suggests price_to_beat was incorrectly parsed.")
            print(f"   Possible causes:")
            print(f"   - Extracted contract price (0.xx) instead of asset price")
            print(f"   - Extracted odds/cents instead of BTC/ETH price")
            print(f"   - Page layout changed")
            print(f"\n   ⚠️  Not safe to trade. Aborting this cycle.")
            return
        
        print(f"✅ Cross-validation passed:")
        print(f"   RTDS current price: ${current_price:.2f}")
        print(f"   Price to beat: ${price_to_beat:.2f}")
        print(f"   Ratio: {price_ratio:.4f} (within acceptable range)")
        
        # Check if time window is suitable
        min_seconds = self.config.get('trading', 'min_seconds_before_close')
        max_seconds = self.config.get('trading', 'max_seconds_before_close')
        
        should_trade, reason = self.strategy.should_trade(seconds_left, min_seconds, max_seconds)
        
        if not should_trade:
            print(f"⏭️  Skipping trade: {reason}")
            return
        
        # Check daily limits
        can_trade, reason = self.stake_manager.can_trade(
            self.state.get('daily_stats', {}),
            self.config.get('safety')
        )
        
        if not can_trade:
            print(f"🛑 Trading blocked: {reason}")
            print("   Run complete. Exiting.")
            self.running = False
            return
        
        # Calculate technical indicators
        df = self.candles.get_dataframe()
        indicators = TechnicalAnalysis.get_indicators(
            df,
            ema_fast=self.config.get('technical_analysis', 'ema_fast'),
            ema_slow=self.config.get('technical_analysis', 'ema_slow'),
            atr_period=self.config.get('technical_analysis', 'atr_period'),
            return_periods=self.config.get('technical_analysis', 'return_periods')
        )
        
        # Make trading decision
        decision_result = self.strategy.make_decision(
            current_price,
            price_to_beat,
            seconds_left,
            indicators
        )
        
        decision = decision_result['decision']
        
        # Get current stake
        stake_amount = self.stake_manager.get_current_stake()
        win_streak = self.stake_manager.get_win_streak()
        
        # Print stake info
        self.stake_manager.print_stake_info()
        
        # Log decision
        self.logger.log_decision({
            'timestamp': datetime.utcnow().isoformat(),
            'asset': self.asset,
            'slug': self.current_slug,
            'current_price': current_price,
            'price_to_beat': price_to_beat,
            'decision': decision,
            'seconds_left': seconds_left,
            'ema9': decision_result.get('ema_fast'),
            'ema20': decision_result.get('ema_slow'),
            'atr': decision_result.get('atr'),
            'return_3m': decision_result.get('return_3m'),
            'return_5m': decision_result.get('return_5m'),
            'gap': decision_result.get('gap'),
            'gap_atr': decision_result.get('gap_atr'),
            'reasoning': decision_result.get('reasoning'),
            'stake_usd': stake_amount,
            'win_streak': win_streak
        })
        
        # Prepare trade in browser
        success = self.ui.prepare_trade(decision, stake_amount)
        
        if not success:
            print("❌ Failed to prepare trade. Aborting cycle.")
            return
        
        # Wait for user confirmation
        confirmed = self.ui.wait_for_confirmation(
            decision,
            stake_amount,
            current_price,
            price_to_beat,
            seconds_left,
            win_streak
        )
        
        if not confirmed:
            print("❌ Trade cancelled by user")
            return
        
        # Execute trade
        executed = self.ui.execute_trade()
        
        # Log trade
        self.logger.log_trade({
            'timestamp': datetime.utcnow().isoformat(),
            'asset': self.asset,
            'slug': self.current_slug,
            'decision': decision,
            'stake_usd': stake_amount,
            'win_streak_before': win_streak,
            'current_price': current_price,
            'price_to_beat': price_to_beat,
            'seconds_left': seconds_left,
            'executed': executed,
            'result': None,  # Will be filled after settlement
            'win_streak_after': None,
            'note': 'Executed' if executed else 'Failed'
        })
        
        if executed:
            print("\n✅ Trade executed successfully!")
            
            # Update state with trade info
            self.state.update(
                last_asset=self.asset,
                last_slug=self.current_slug,
                last_decision=decision,
                last_timestamp=datetime.utcnow().isoformat()
            )
            
            # Wait for settlement and ask for result
            self._handle_trade_result(stake_amount)
        else:
            print("\n❌ Trade execution failed")
    
    def _update_candles(self):
        """Update candles with latest price data."""
        ticks = self.rtds.get_all_prices()
        
        for tick in ticks:
            self.candles.add_tick(tick['price'], tick['timestamp'])
    
    def _handle_trade_result(self, stake_used: float):
        """Handle trade result determination and stake update.
        
        Args:
            stake_used: Stake amount used in trade
        """
        result_mode = self.config.get('stake', 'result_mode', 'manual')
        
        if result_mode == 'manual':
            # Ask user for result
            result = self.stake_manager.ask_for_result()
            
            # Update stake based on result
            update_info = self.stake_manager.update_after_result(result, stake_used)
            
            # Log result
            self.logger.log_trade({
                'timestamp': datetime.utcnow().isoformat(),
                'asset': self.asset,
                'slug': self.current_slug,
                'decision': self.state.get('last_decision'),
                'stake_usd': stake_used,
                'win_streak_before': self.state.get('win_streak', 0) - (1 if result == 'W' else 0),
                'current_price': None,
                'price_to_beat': None,
                'seconds_left': None,
                'executed': True,
                'result': result,
                'win_streak_after': update_info['new_streak'],
                'note': f"Result recorded: {result}, PNL: ${update_info['pnl']:+.2f}"
            })
        
        else:
            print("⚠️  Auto result mode not implemented yet. Please manually update result.")
    
    def _cleanup(self):
        """Cleanup resources."""
        print("\n🧹 Cleaning up...")
        
        if self.rtds:
            self.rtds.stop()
        
        if self.ui:
            self.ui.stop_browser()
        
        print("✅ Cleanup complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Polymarket One-Click Bot')
    parser.add_argument(
        '--asset',
        type=str,
        required=True,
        choices=['btc', 'eth'],
        help='Asset to trade (btc or eth)'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Enable watch mode for continuous trading'
    )
    
    args = parser.parse_args()
    
    # Create and run bot
    bot = PolymrketBot(args.asset, args.watch)
    bot.run()
    
    print("\n👋 Bot stopped. Goodbye!")


if __name__ == '__main__':
    main()
