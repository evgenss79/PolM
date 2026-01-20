"""
Gamma API client for discovering active Polymarket markets.

Two-level discovery for 15m crypto markets:
1. Primary: Gamma API with proper ordering and filtering
2. Fallback: UI scraping from polymarket.com/crypto/15m
"""

import requests
import time
import traceback
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
        Filters out future markets by checking startDate/endDate to only select live markets.
        
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
            
            # Filter by time: only keep markets that are LIVE NOW (start <= now < end)
            now = datetime.utcnow()
            live_markets = []
            
            for market in matching:
                is_live = self._is_market_live(market, now)
                if is_live:
                    live_markets.append(market)
            
            print(f"   📊 After LIVE NOW filter: {len(live_markets)} markets (filtered out {len(matching) - len(live_markets)} future/past markets)")
            
            if not live_markets:
                print(f"❌ PRIMARY DISCOVERY FAILED: No LIVE markets found (all {len(matching)} candidates are future or past markets)")
                print(f"   This typically means:")
                print(f"   - Future markets scheduled but not started yet")
                print(f"   - API indexing delay for new rounds")
                print(f"   Falling back to UI scraping...")
                return None
            
            # Sort by most recent (newest first) - double-check ordering
            # Markets have 'id' field which increases with time
            live_markets.sort(key=lambda x: x.get('id', 0), reverse=True)
            
            # Get the most recent LIVE market
            market = live_markets[0]
            slug = market.get('slug')
            question = market.get('question', 'N/A')
            market_id = market.get('id', 'N/A')
            
            # Extract timestamp from slug for validation
            timestamp_info = self._extract_timestamp_from_slug(slug)
            
            # Log selection reasoning
            start_time_str = self._format_market_time(market, 'start')
            end_time_str = self._format_market_time(market, 'end')
            
            print(f"✅ PRIMARY DISCOVERY SUCCESS!")
            print(f"   Selected: LIVE market (start <= now < end)")
            print(f"   Slug: {slug}")
            print(f"   Question: {question}")
            print(f"   Market ID: {market_id}")
            if timestamp_info:
                print(f"   Timestamp: {timestamp_info}")
            if start_time_str:
                print(f"   Start: {start_time_str}")
            if end_time_str:
                print(f"   End: {end_time_str}")
            print(f"   Reason: This market is LIVE NOW (among {len(live_markets)} live options)")
            
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
    
    def _is_market_live(self, market: Dict[str, Any], now: datetime) -> bool:
        """Check if a market is currently live (start <= now < end).
        
        Args:
            market: Market dictionary from Gamma API
            now: Current UTC datetime
        
        Returns:
            True if market is live now, False otherwise
        """
        try:
            # Parse start time from market data
            # Fields can be: startDate, startTime, or combined timestamp fields
            start_dt = self._parse_market_datetime(market, 'start')
            end_dt = self._parse_market_datetime(market, 'end')
            
            # If we can't parse times, assume it's live (fail-open for backward compatibility)
            if start_dt is None or end_dt is None:
                return True
            
            # Check if market is live: start <= now < end
            return start_dt <= now < end_dt
            
        except Exception as e:
            # If parsing fails, assume market is live (fail-open)
            print(f"   ⚠️  Could not parse market times, assuming live: {e}")
            return True
    
    def _parse_market_datetime(self, market: Dict[str, Any], time_type: str) -> Optional[datetime]:
        """Parse start or end datetime from market data.
        
        Args:
            market: Market dictionary from Gamma API
            time_type: 'start' or 'end'
        
        Returns:
            Parsed datetime or None if not available
        """
        try:
            # Try different field name patterns
            # Pattern 1: startDate/endDate as ISO string
            date_field = f"{time_type}Date"
            if date_field in market and market[date_field]:
                # ISO format: "2026-01-20T14:30:00Z" or timestamp
                date_str = market[date_field]
                if isinstance(date_str, str):
                    # Try parsing ISO format
                    try:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                    # Try parsing as Unix timestamp string
                    try:
                        return datetime.utcfromtimestamp(float(date_str))
                    except (ValueError, OSError, OverflowError):
                        pass
                elif isinstance(date_str, (int, float)):
                    # Unix timestamp
                    return datetime.utcfromtimestamp(date_str)
            
            # Pattern 2: Separate date and time fields (startDate + startTime)
            date_field = f"{time_type}Date"
            time_field = f"{time_type}Time"
            if date_field in market and time_field in market:
                date_val = market[date_field]
                time_val = market[time_field]
                if date_val and time_val:
                    # Combine date and time strings
                    datetime_str = f"{date_val} {time_val}"
                    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            
            # Pattern 3: Single timestamp field (e.g., "startTimestamp")
            timestamp_field = f"{time_type}Timestamp"
            if timestamp_field in market and market[timestamp_field]:
                ts = market[timestamp_field]
                if isinstance(ts, (int, float)):
                    return datetime.utcfromtimestamp(ts)
                elif isinstance(ts, str):
                    try:
                        return datetime.utcfromtimestamp(float(ts))
                    except (ValueError, OSError, OverflowError):
                        pass
            
            return None
            
        except Exception as e:
            return None
    
    def _format_market_time(self, market: Dict[str, Any], time_type: str) -> Optional[str]:
        """Format start or end time for display.
        
        Args:
            market: Market dictionary
            time_type: 'start' or 'end'
        
        Returns:
            Formatted time string or None
        """
        dt = self._parse_market_datetime(market, time_type)
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        return None
    
    def discover_15m_event_via_ui(
        self,
        asset: str,
        page,  # Type: playwright.sync_api.Page (avoid import dependency)
        base_url: str,
        page_load_delay: int = 2
    ) -> Optional[Dict[str, Any]]:
        """FALLBACK discovery: Scrape event from polymarket.com/crypto/15m page.
        
        This is used when Gamma API fails to return fresh 15m events.
        
        Args:
            asset: Asset name ('BTC' or 'ETH')
            page: Playwright Page object (playwright.sync_api.Page)
            base_url: Polymarket base URL
            page_load_delay: Seconds to wait after page load (default: 2)
        
        Returns:
            Dictionary with event info or None if failed
        """
        try:
            print(f"\n🔄 FALLBACK DISCOVERY: Scraping UI for {asset} 15m event...")
            
            # Navigate to the 15m crypto aggregator page
            crypto_15m_url = f"{base_url}/crypto/15m"
            print(f"   📍 Navigating to: {crypto_15m_url}")
            # Use domcontentloaded instead of networkidle because Polymarket has live websockets
            page.goto(crypto_15m_url, wait_until='domcontentloaded', timeout=90000)
            
            # Wait for page to stabilize
            page.wait_for_timeout(1500)
            
            # Wait for page to fully load (allow dynamic content to render)
            time.sleep(page_load_delay)
            
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
                    # Use count() and nth() for better memory efficiency
                    links_locator = page.locator('a[href*="/event/"]')
                    link_count = links_locator.count()
                    
                    for i in range(link_count):
                        try:
                            link = links_locator.nth(i)
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
