"""
Robust selectors for Polymarket page elements.
"""

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Tuple
import re


class Selectors:
    """Robust element selectors for Polymarket pages."""
    
    @staticmethod
    def find_price_to_beat(page: Page, timeout: int = 10000, asset: Optional[str] = None) -> Optional[float]:
        """Find 'PRICE TO BEAT' value on the page with strict label-based extraction.
        
        Per task requirements:
        - Parse "Price to beat" ONLY from UI near the label "Price to beat"
        - Do NOT extract from contract prices (0.xx), cents, or odds
        - Add strict sanity checks: BTC > 10000, ETH > 500
        
        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds
            asset: Asset type ('btc' or 'eth') for sanity checks
        
        Returns:
            Price value or None if not found / validation failed
        """
        try:
            print("🔍 Parsing 'Price to beat' with label-based extraction...")
            
            # Look for text containing "PRICE TO BEAT" or "Price to beat"
            # Then find the price value nearby
            
            # Try multiple strategies
            strategies = [
                # Strategy 1: Look for exact text
                lambda: page.locator("text=/PRICE TO BEAT/i").first,
                # Strategy 2: Look in headers/labels
                lambda: page.locator("h3, h4, label, div, span").filter(has_text=re.compile(r"price to beat", re.I)).first,
            ]
            
            parsed_value = None
            context_text = None
            
            for strategy in strategies:
                try:
                    element = strategy()
                    element.wait_for(timeout=timeout)
                    
                    # Look for price pattern nearby (in parent container)
                    parent = element.locator('xpath=../..')
                    context_text = parent.inner_text()
                    
                    # Extract price (formats: $1,234.56 or 1234.56)
                    # Look for large numbers (crypto prices are typically > 100)
                    matches = re.findall(r'\$?([\d,]+\.?\d*)', context_text)
                    
                    for match in matches:
                        price_str = match.replace(',', '')
                        try:
                            price = float(price_str)
                            
                            # Skip obviously wrong values:
                            # - Contract prices (0.xx range)
                            # - Cents (< 1.00)
                            # - Small odds values (< 10)
                            if price < 10:
                                continue
                            
                            # This looks like a real price, use it
                            parsed_value = price
                            break
                        except ValueError:
                            continue
                    
                    if parsed_value:
                        break
                
                except PlaywrightTimeoutError:
                    continue
            
            if parsed_value is None:
                print("⚠️  Could not find price to beat on page")
                return None
            
            # Sanity check validation per task requirements
            if asset:
                asset_lower = asset.lower()
                
                if asset_lower == 'btc' and parsed_value <= 10000:
                    print(f"❌ VALIDATION FAILED: BTC price to beat ({parsed_value:.2f}) is <= 10000")
                    print(f"   This looks like contract price/odds, not BTC price.")
                    print(f"   Context: {context_text[:200]}")
                    return None
                
                elif asset_lower == 'eth' and parsed_value <= 500:
                    print(f"❌ VALIDATION FAILED: ETH price to beat ({parsed_value:.2f}) is <= 500")
                    print(f"   This looks like contract price/odds, not ETH price.")
                    print(f"   Context: {context_text[:200]}")
                    return None
            
            # Additional sanity check: if value is between 0 and 1, it's likely a contract price
            if 0 < parsed_value < 1:
                print(f"❌ VALIDATION FAILED: Parsed value {parsed_value:.2f} is in contract price range (0.xx)")
                print(f"   This is NOT a price to beat. Aborting.")
                print(f"   Context: {context_text[:200]}")
                return None
            
            print(f"✅ Found and validated price to beat: ${parsed_value:.2f}")
            return parsed_value
        
        except Exception as e:
            print(f"❌ Error finding price to beat: {e}")
            return None
    
    @staticmethod
    def find_countdown(page: Page, timeout: int = 10000) -> Optional[int]:
        """Find countdown timer and convert to seconds.
        
        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds
        
        Returns:
            Seconds remaining or None if not found
        """
        try:
            # Look for countdown patterns: "MM:SS" or "HH:MM:SS"
            # Common patterns: "08:49", "0:08:49", "8m 49s"
            
            # Try to find timer elements
            strategies = [
                # Strategy 1: Look for time pattern
                lambda: page.locator("text=/\\d+:\\d+/").first,
                # Strategy 2: Look for elements with "min" or "sec"
                lambda: page.locator("text=/\\d+\\s*(min|sec|m|s)/i").first,
            ]
            
            for strategy in strategies:
                try:
                    element = strategy()
                    element.wait_for(timeout=timeout)
                    text = element.inner_text()
                    
                    # Parse different formats
                    # Format 1: "MM:SS"
                    match = re.search(r'(\d+):(\d+)', text)
                    if match:
                        minutes = int(match.group(1))
                        seconds = int(match.group(2))
                        total_seconds = minutes * 60 + seconds
                        print(f"✅ Found countdown: {minutes}m {seconds}s ({total_seconds}s)")
                        return total_seconds
                    
                    # Format 2: "Xm Ys"
                    match = re.search(r'(\d+)\s*m.*?(\d+)\s*s', text, re.I)
                    if match:
                        minutes = int(match.group(1))
                        seconds = int(match.group(2))
                        total_seconds = minutes * 60 + seconds
                        print(f"✅ Found countdown: {minutes}m {seconds}s ({total_seconds}s)")
                        return total_seconds
                
                except PlaywrightTimeoutError:
                    continue
            
            print("⚠️  Could not find countdown on page")
            return None
        
        except Exception as e:
            print(f"❌ Error finding countdown: {e}")
            return None
    
    @staticmethod
    def find_current_price_display(page: Page, timeout: int = 10000) -> Optional[float]:
        """Find current price display on the page.
        
        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds
        
        Returns:
            Current price or None if not found
        """
        try:
            # Look for "Current Price" or similar labels
            strategies = [
                lambda: page.locator("text=/current price/i").first,
                lambda: page.locator("text=/live price/i").first,
            ]
            
            for strategy in strategies:
                try:
                    element = strategy()
                    element.wait_for(timeout=timeout)
                    
                    parent = element.locator('xpath=../..')
                    text = parent.inner_text()
                    
                    match = re.search(r'\$?([\d,]+\.?\d*)', text)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        price = float(price_str)
                        print(f"✅ Found current price display: ${price:.2f}")
                        return price
                
                except PlaywrightTimeoutError:
                    continue
            
            return None
        
        except Exception as e:
            print(f"❌ Error finding current price display: {e}")
            return None
    
    @staticmethod
    def find_outcome_button(page: Page, outcome: str, timeout: int = 10000) -> Optional[Locator]:
        """Find Up or Down outcome button.
        
        Args:
            page: Playwright page object
            outcome: 'UP' or 'DOWN'
            timeout: Timeout in milliseconds
        
        Returns:
            Button locator or None if not found
        """
        try:
            outcome = outcome.upper()
            
            # Try different selector strategies
            strategies = [
                # Strategy 1: Button with text
                lambda: page.locator(f"button:has-text('{outcome}')").first,
                # Strategy 2: Any clickable with text
                lambda: page.locator(f"text={outcome}").locator('xpath=..').filter(has=page.locator("button")).first,
                # Strategy 3: Case insensitive
                lambda: page.locator(f"button").filter(has_text=re.compile(f"^{outcome}$", re.I)).first,
            ]
            
            for strategy in strategies:
                try:
                    button = strategy()
                    button.wait_for(timeout=timeout, state='visible')
                    print(f"✅ Found {outcome} button")
                    return button
                except PlaywrightTimeoutError:
                    continue
            
            print(f"⚠️  Could not find {outcome} button")
            return None
        
        except Exception as e:
            print(f"❌ Error finding {outcome} button: {e}")
            return None
    
    @staticmethod
    def find_amount_input(page: Page, timeout: int = 10000) -> Optional[Locator]:
        """Find amount input field.
        
        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds
        
        Returns:
            Input locator or None if not found
        """
        try:
            # Look for input fields with placeholder or label containing "amount"
            strategies = [
                lambda: page.locator("input[placeholder*='amount' i]").first,
                lambda: page.locator("input[type='number']").first,
                lambda: page.locator("input[placeholder*='USD' i]").first,
                lambda: page.locator("label:has-text('Amount')").locator('xpath=..').locator('input').first,
            ]
            
            for strategy in strategies:
                try:
                    input_field = strategy()
                    input_field.wait_for(timeout=timeout, state='visible')
                    print(f"✅ Found amount input field")
                    return input_field
                except PlaywrightTimeoutError:
                    continue
            
            print(f"⚠️  Could not find amount input field")
            return None
        
        except Exception as e:
            print(f"❌ Error finding amount input: {e}")
            return None
    
    @staticmethod
    def find_buy_button(page: Page, timeout: int = 10000) -> Optional[Locator]:
        """Find Buy button (final confirmation).
        
        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds
        
        Returns:
            Button locator or None if not found
        """
        try:
            # Look for button with "Buy" text
            strategies = [
                lambda: page.locator("button:has-text('Buy')").first,
                lambda: page.locator("button").filter(has_text=re.compile(r"buy", re.I)).first,
                lambda: page.locator("button:has-text('Place order')").first,
                lambda: page.locator("button:has-text('Confirm')").first,
            ]
            
            for strategy in strategies:
                try:
                    button = strategy()
                    button.wait_for(timeout=timeout, state='visible')
                    
                    # Check if button is enabled
                    if button.is_enabled():
                        print(f"✅ Found Buy button")
                        return button
                except PlaywrightTimeoutError:
                    continue
            
            print(f"⚠️  Could not find enabled Buy button")
            return None
        
        except Exception as e:
            print(f"❌ Error finding Buy button: {e}")
            return None
