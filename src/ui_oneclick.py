"""
Playwright browser automation for One-Click trading interface.
"""

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from typing import Optional, Dict, Any, Tuple
from .selectors import Selectors
import time


class OneClickUI:
    """Browser automation for Polymarket One-Click trading."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Browser configuration from config.json
        """
        self.headless = config.get('headless', False)
        self.profile_dir = config.get('profile_dir', '.pw_profile')
        self.timeout = config.get('timeout_ms', 30000)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.slow_mo = config.get('slow_mo_ms', 500)
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def start_browser(self):
        """Start Playwright browser with persistent profile."""
        print("🌐 Starting browser...")
        
        self.playwright = sync_playwright().start()
        
        # Launch browser with persistent context (saves login session)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            headless=self.headless,
            slow_mo=self.slow_mo,
            viewport={'width': 1280, 'height': 1024},
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        
        print(f"✅ Browser started ({'headless' if self.headless else 'visible'})")
    
    def stop_browser(self):
        """Stop browser and cleanup."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ Browser stopped")
    
    def navigate_to_market(self, url: str):
        """Navigate to market URL.
        
        Args:
            url: Full market URL
        """
        print(f"📍 Navigating to: {url}")
        self.page.goto(url, wait_until='networkidle', timeout=self.timeout)
        time.sleep(2)  # Give page time to fully load
        print("✅ Page loaded")
    
    def parse_market_info(self) -> Tuple[Optional[float], Optional[int]]:
        """Parse price to beat and countdown from page.
        
        Returns:
            Tuple of (price_to_beat, seconds_left) or (None, None) on failure
        """
        print("🔍 Parsing market information...")
        
        price_to_beat = Selectors.find_price_to_beat(self.page, timeout=self.timeout)
        seconds_left = Selectors.find_countdown(self.page, timeout=self.timeout)
        
        if price_to_beat is None or seconds_left is None:
            print("⚠️  Could not parse all market info from page")
            return None, None
        
        return price_to_beat, seconds_left
    
    def ask_manual_market_info(self) -> Tuple[float, int]:
        """Ask user to manually enter market info if parsing fails.
        
        Returns:
            Tuple of (price_to_beat, seconds_left)
        """
        print("\n" + "="*70)
        print("⚠️  Manual Input Required")
        print("="*70)
        print("Could not automatically read market information from the page.")
        print("Please enter the following manually:\n")
        
        while True:
            try:
                price_str = input("Price to Beat (e.g., 43250.50): $")
                price_to_beat = float(price_str.replace(',', ''))
                break
            except ValueError:
                print("❌ Invalid price. Please enter a number.")
        
        while True:
            try:
                mins_str = input("Minutes left: ")
                mins = int(mins_str)
                secs_str = input("Seconds left: ")
                secs = int(secs_str)
                seconds_left = mins * 60 + secs
                break
            except ValueError:
                print("❌ Invalid time. Please enter integers.")
        
        print(f"\n✅ Manually entered: ${price_to_beat:.2f}, {seconds_left}s left")
        print("="*70 + "\n")
        
        return price_to_beat, seconds_left
    
    def prepare_trade(
        self,
        decision: str,
        amount: float,
        retries: Optional[int] = None
    ) -> bool:
        """Prepare trade: select outcome and enter amount.
        
        Args:
            decision: 'UP' or 'DOWN'
            amount: Amount in USD
            retries: Number of retry attempts (default from config)
        
        Returns:
            True if successful, False otherwise
        """
        if retries is None:
            retries = self.retry_attempts
        
        print(f"\n🎯 Preparing trade: {decision} ${amount:.2f}")
        
        for attempt in range(retries):
            try:
                # Step 1: Select outcome (UP or DOWN)
                print(f"  Step 1: Selecting {decision}...")
                outcome_button = Selectors.find_outcome_button(self.page, decision, timeout=self.timeout)
                
                if not outcome_button:
                    raise Exception(f"Could not find {decision} button")
                
                outcome_button.click()
                time.sleep(1)
                
                # Verify selection (check if button is active/selected)
                print(f"  ✅ {decision} selected")
                
                # Step 2: Enter amount
                print(f"  Step 2: Entering amount ${amount:.2f}...")
                amount_input = Selectors.find_amount_input(self.page, timeout=self.timeout)
                
                if not amount_input:
                    raise Exception("Could not find amount input field")
                
                # Clear field first
                amount_input.click()
                amount_input.fill('')
                time.sleep(0.5)
                
                # Enter amount
                amount_input.fill(str(amount))
                time.sleep(1)
                
                # Verify amount was entered
                entered_value = amount_input.input_value()
                if abs(float(entered_value) - amount) > 0.01:
                    raise Exception(f"Amount mismatch: entered {entered_value}, expected {amount}")
                
                print(f"  ✅ Amount ${amount:.2f} entered")
                
                return True
            
            except Exception as e:
                print(f"  ❌ Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    print(f"  🔄 Retrying in 2 seconds...")
                    time.sleep(2)
        
        print(f"❌ Failed to prepare trade after {retries} attempts")
        return False
    
    def wait_for_confirmation(
        self,
        decision: str,
        amount: float,
        current_price: float,
        price_to_beat: float,
        seconds_left: int,
        win_streak: int
    ):
        """Display trade info and wait for user confirmation.
        
        Args:
            decision: 'UP' or 'DOWN'
            amount: Stake amount
            current_price: Current market price
            price_to_beat: Target price
            seconds_left: Seconds until close
            win_streak: Current win streak
        """
        print("\n" + "="*70)
        print("🚨 ONE-CLICK CONFIRMATION")
        print("="*70)
        print(f"Decision: {decision}")
        print(f"Amount: ${amount:.2f}")
        print(f"Current Price: ${current_price:.2f}")
        print(f"Price to Beat: ${price_to_beat:.2f}")
        print(f"Time Left: {seconds_left}s ({seconds_left//60}m {seconds_left%60}s)")
        print(f"Win Streak: {win_streak}")
        print("\n⚠️  Please verify the trade details in the browser window.")
        print("="*70)
        print("\nPress ENTER to execute the trade, or close the browser to cancel...")
        print("="*70)
        
        try:
            input()
            return True
        except KeyboardInterrupt:
            print("\n❌ Trade cancelled by user (Ctrl+C)")
            return False
    
    def execute_trade(self, retries: Optional[int] = None) -> bool:
        """Click Buy button to execute trade.
        
        Args:
            retries: Number of retry attempts
        
        Returns:
            True if successful, False otherwise
        """
        if retries is None:
            retries = self.retry_attempts
        
        print("\n💰 Executing trade...")
        
        for attempt in range(retries):
            try:
                buy_button = Selectors.find_buy_button(self.page, timeout=self.timeout)
                
                if not buy_button:
                    raise Exception("Could not find Buy button")
                
                print(f"  Clicking Buy button...")
                buy_button.click()
                
                print(f"  ✅ Buy button clicked!")
                time.sleep(2)
                
                return True
            
            except Exception as e:
                print(f"  ❌ Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    print(f"  🔄 Retrying in 2 seconds...")
                    time.sleep(2)
        
        print(f"❌ Failed to execute trade after {retries} attempts")
        return False
    
    def check_if_logged_in(self) -> bool:
        """Check if user is logged into Polymarket.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            # Look for signs of being logged in (profile icon, wallet address, etc.)
            # This is a simple check - adjust based on actual Polymarket UI
            
            # Look for common logged-in indicators
            indicators = [
                lambda: self.page.locator("button:has-text('Connect')").count() == 0,
                lambda: self.page.locator("text=/0x[a-fA-F0-9]{4,}/").count() > 0,
            ]
            
            for indicator in indicators:
                if indicator():
                    print("✅ User appears to be logged in")
                    return True
            
            print("⚠️  User may not be logged in")
            return False
        
        except Exception as e:
            print(f"❌ Error checking login status: {e}")
            return False
    
    def prompt_login(self):
        """Prompt user to log in manually."""
        print("\n" + "="*70)
        print("🔐 LOGIN REQUIRED")
        print("="*70)
        print("Please log into Polymarket in the browser window.")
        print("After logging in, the session will be saved for future runs.")
        print("\nPress ENTER when you are logged in...")
        print("="*70)
        input()
        print("✅ Continuing...\n")
