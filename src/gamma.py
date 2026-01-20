"""
Gamma API client for discovering active Polymarket markets.

Two-level discovery for 15m crypto markets:
1. Primary: Gamma API with proper ordering and filtering
2. Fallback: UI scraping from polymarket.com/crypto/15m
"""

import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import re


class GammaAPI:
    """Client for Polymarket Gamma API to find active markets."""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def find_active_market(self, slug_prefix: str) -> Optional[Dict[str, Any]]:
        """Find the most recent active market matching slug prefix (PRIMARY discovery).
        
        Uses enhanced Gamma API query with proper ordering to find fresh 15m events.
        
        Args:
            slug_prefix: Market slug prefix (e.g., "btc-updown-15m-")
        
        Returns:
            Market data dictionary or None if not found
        """
        try:
            print(f"🔍 PRIMARY DISCOVERY: Searching Gamma API for prefix: {slug_prefix}")
            
            # Query Gamma API with enhanced parameters for 15m discovery
            response = requests.get(
                self.api_url,
                params={
                    "closed": "false",      # Only active markets
                    "limit": 100,           # Increased limit for better coverage
                    "order": "id",          # Order by ID (newest events have higher IDs)
                    "ascending": "false"    # Descending order (newest first)
                },
                timeout=10
            )
            response.raise_for_status()
            
            markets = response.json()
            print(f"   📊 Gamma API returned {len(markets)} total markets")
            
            # Filter markets by slug prefix
            matching = [
                m for m in markets 
                if m.get('slug', '').startswith(slug_prefix)
            ]
            
            print(f"   📊 Found {len(matching)} markets matching prefix '{slug_prefix}'")
            
            if not matching:
                print(f"❌ PRIMARY DISCOVERY FAILED: No active markets found for prefix: {slug_prefix}")
                return None
            
            # Sort by most recent (newest first) - double-check ordering
            # Markets have 'id' field which increases with time
            matching.sort(key=lambda x: x.get('id', 0), reverse=True)
            
            # Get the most recent market
            market = matching[0]
            slug = market.get('slug')
            question = market.get('question', 'N/A')
            market_id = market.get('id', 'N/A')
            
            # Extract timestamp from slug for validation
            timestamp_info = self._extract_timestamp_from_slug(slug)
            
            print(f"✅ PRIMARY DISCOVERY SUCCESS!")
            print(f"   Slug: {slug}")
            print(f"   Question: {question}")
            print(f"   Market ID: {market_id}")
            if timestamp_info:
                print(f"   Timestamp: {timestamp_info}")
            
            return market
            
        except requests.RequestException as e:
            print(f"❌ PRIMARY DISCOVERY ERROR: Failed to fetch from Gamma API: {e}")
            return None
        except Exception as e:
            print(f"❌ PRIMARY DISCOVERY ERROR: Unexpected error: {e}")
            return None
    
    def get_market_url(self, slug: str, base_url: str) -> str:
        """Construct full market URL from slug.
        
        Args:
            slug: Market slug
            base_url: Polymarket base URL
        
        Returns:
            Full market URL
        """
        return f"{base_url}/event/{slug}"
    
    def watch_for_new_market(
        self, 
        slug_prefix: str, 
        current_slug: str
    ) -> Optional[Dict[str, Any]]:
        """Check if a new market has appeared (different from current).
        
        Args:
            slug_prefix: Market slug prefix
            current_slug: Currently tracked slug
        
        Returns:
            New market data if found, None otherwise
        """
        market = self.find_active_market(slug_prefix)
        
        if market and market.get('slug') != current_slug:
            print(f"🆕 New market detected: {market.get('slug')}")
            return market
        
        return None
    
    def _extract_timestamp_from_slug(self, slug: str) -> Optional[str]:
        """Extract timestamp from 15m crypto slug.
        
        Args:
            slug: Event slug (e.g., "btc-updown-15m-jan20-1430" or "btc-updown-15m-1234567890")
        
        Returns:
            Timestamp string or None if not extractable
        """
        try:
            # Pattern for 15m crypto slugs
            # Format: {asset}-updown-15m-{timestamp}
            # Timestamp can be various formats (jan20-1430, 1234567890, etc.)
            match = re.search(r'-15m-(.+)$', slug)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None
    
    def discover_15m_event_via_ui(
        self,
        asset: str,
        page,  # Playwright Page object
        base_url: str
    ) -> Optional[Dict[str, Any]]:
        """FALLBACK discovery: Scrape event from polymarket.com/crypto/15m page.
        
        This is used when Gamma API fails to return fresh 15m events.
        
        Args:
            asset: Asset name ('BTC' or 'ETH')
            page: Playwright Page object
            base_url: Polymarket base URL
        
        Returns:
            Dictionary with event info or None if failed
        """
        try:
            print(f"\n🔄 FALLBACK DISCOVERY: Scraping UI for {asset} 15m event...")
            
            # Navigate to the 15m crypto aggregator page
            crypto_15m_url = f"{base_url}/crypto/15m"
            print(f"   📍 Navigating to: {crypto_15m_url}")
            page.goto(crypto_15m_url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to fully load
            import time
            time.sleep(2)
            
            # Look for the asset card (Bitcoin or Ethereum)
            asset_names = {
                'BTC': ['Bitcoin', 'BTC'],
                'ETH': ['Ethereum', 'ETH']
            }
            
            search_terms = asset_names.get(asset.upper(), [asset])
            
            print(f"   🔍 Looking for {asset} event card...")
            
            event_href = None
            
            # Try to find event link using multiple strategies
            for term in search_terms:
                try:
                    # Strategy 1: Find card containing the asset name and get its link
                    # Look for links with /event/ in href
                    links = page.locator('a[href*="/event/"]').all()
                    
                    for link in links:
                        try:
                            # Get the href
                            href = link.get_attribute('href')
                            if not href:
                                continue
                            
                            # Check if this link is related to our asset
                            # by looking at the slug pattern
                            slug_pattern = f"{asset.lower()}-updown-15m-"
                            if slug_pattern in href:
                                event_href = href
                                print(f"   ✅ Found {asset} event link: {href}")
                                break
                        except Exception:
                            continue
                    
                    if event_href:
                        break
                        
                except Exception as e:
                    print(f"   ⚠️  Strategy failed for term '{term}': {e}")
                    continue
            
            if not event_href:
                print(f"❌ FALLBACK DISCOVERY FAILED: Could not find {asset} event on {crypto_15m_url}")
                return None
            
            # Parse the event info
            # href format: /event/btc-updown-15m-XXXXXXXX
            if event_href.startswith('/'):
                event_href = event_href[1:]  # Remove leading slash
            
            # Extract slug from href
            slug = event_href.replace('event/', '')
            
            # Extract timestamp
            timestamp_info = self._extract_timestamp_from_slug(slug)
            
            # Construct full URL
            full_url = f"{base_url}/event/{slug}"
            
            result = {
                'slug': slug,
                'url': full_url,
                'asset': asset.upper(),
                'timestamp': timestamp_info,
                'source': 'UI_FALLBACK'
            }
            
            print(f"✅ FALLBACK DISCOVERY SUCCESS!")
            print(f"   Slug: {slug}")
            print(f"   URL: {full_url}")
            print(f"   Asset: {asset.upper()}")
            if timestamp_info:
                print(f"   Timestamp: {timestamp_info}")
            
            return result
            
        except Exception as e:
            print(f"❌ FALLBACK DISCOVERY ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def discover_15m_market(
        self,
        asset: str,
        slug_prefix: str,
        page=None,  # Optional Playwright Page for fallback
        base_url: str = "https://polymarket.com"
    ) -> Optional[Dict[str, Any]]:
        """Two-level discovery for 15m crypto markets.
        
        LEVEL 1 (Primary): Try Gamma API with enhanced filtering
        LEVEL 2 (Fallback): Scrape UI from polymarket.com/crypto/15m
        
        Args:
            asset: Asset name ('BTC' or 'ETH')
            slug_prefix: Market slug prefix (e.g., "btc-updown-15m-")
            page: Optional Playwright Page object for UI fallback
            base_url: Polymarket base URL
        
        Returns:
            Dictionary with market/event info, or None if both methods fail
        """
        print("\n" + "="*70)
        print(f"🔍 TWO-LEVEL DISCOVERY FOR {asset.upper()} 15m MARKET")
        print("="*70)
        
        # LEVEL 1: Try Gamma API (Primary)
        print("\n📊 LEVEL 1: Gamma API Discovery")
        print("-" * 70)
        market = self.find_active_market(slug_prefix)
        
        if market:
            # Success with Gamma API
            slug = market.get('slug')
            full_url = self.get_market_url(slug, base_url)
            
            result = {
                'slug': slug,
                'url': full_url,
                'asset': asset.upper(),
                'timestamp': self._extract_timestamp_from_slug(slug),
                'source': 'GAMMA_API',
                'market_data': market
            }
            
            print("\n✅ Discovery complete via Gamma API")
            print("="*70 + "\n")
            return result
        
        # LEVEL 2: Fallback to UI scraping
        print("\n🔄 LEVEL 2: UI Fallback Discovery")
        print("-" * 70)
        print("⚠️  Gamma API did not return any matching events.")
        print("   This can happen when:")
        print("   - New 15m round just started (indexing delay)")
        print("   - Gamma API is having issues")
        print("   - Market slug format changed")
        print("\n   Attempting UI scraping from polymarket.com/crypto/15m...")
        
        if not page:
            print("❌ FALLBACK FAILED: No browser page provided for UI scraping")
            print("   To use fallback discovery, browser must be started first.")
            print("\n❌ DISCOVERY FAILED: Both Gamma API and UI fallback unavailable")
            print("="*70 + "\n")
            return None
        
        event_info = self.discover_15m_event_via_ui(asset, page, base_url)
        
        if event_info:
            print("\n✅ Discovery complete via UI fallback")
            print("="*70 + "\n")
            return event_info
        
        # Both methods failed
        print("\n❌ DISCOVERY FAILED: Both Gamma API and UI fallback failed")
        print("="*70 + "\n")
        return None
