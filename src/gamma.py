"""
Gamma API client for discovering active Polymarket markets.

Two-level discovery for 15m crypto markets:
1. Primary: Official Gamma /events API with proper LIVE NOW filtering
2. Fallback: UI scraping from polymarket.com/crypto/15m (when events API fails)
"""

import requests
import time
import traceback
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
import re


class GammaAPI:
    """Client for Polymarket Gamma API to find active markets."""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        # Events endpoint for official discovery
        self.events_url = api_url.replace('/markets', '/events')
        # Markets endpoint for detailed market info
        self.markets_url = api_url
    
    def discover_15m_event_via_events_api(
        self,
        slug_prefix: str,
        max_candidates: int = 10,
        max_pages: int = 5
    ) -> Optional[Dict[str, Any]]:
        """PRIMARY discovery: Fetch events from official Gamma /events API.
        
        Uses Polymarket's official /events endpoint with proper filtering and pagination.
        Implements LIVE NOW filtering with timezone-aware UTC comparisons.
        
        Args:
            slug_prefix: Market slug prefix (e.g., "btc-updown-15m-")
            max_candidates: Stop pagination after finding N candidates (default: 10)
            max_pages: Maximum pages to fetch (default: 5)
        
        Returns:
            Event/market data dictionary or None if not found
        """
        try:
            print(f"🔍 PRIMARY DISCOVERY: Fetching from Gamma /events API for prefix: {slug_prefix}")
            
            all_candidates = []
            offset = 0
            limit = 200
            page = 0
            
            # Pagination loop
            while page < max_pages:
                page += 1
                
                # Fetch events from API with official parameters
                response = requests.get(
                    self.events_url,
                    params={
                        "active": "true",        # Only active events
                        "closed": "false",       # Exclude closed events
                        "order": "id",           # Order by ID
                        "ascending": "false",    # Descending (newest first)
                        "limit": limit,
                        "offset": offset
                    },
                    timeout=10
                )
                response.raise_for_status()
                
                events = response.json()
                print(f"   📊 Events discovery: fetched {len(events)} events (page {page}, offset={offset})")
                
                if not events:
                    print(f"   ℹ️  No more events returned (pagination complete)")
                    break
                
                # Extract candidates from events
                page_candidates = self._extract_candidates_from_events(events, slug_prefix)
                all_candidates.extend(page_candidates)
                
                print(f"   📊 Candidates by prefix: +{len(page_candidates)} (total: {len(all_candidates)})")
                
                # Stop if we have enough candidates
                if len(all_candidates) >= max_candidates:
                    print(f"   ✅ Found {len(all_candidates)} candidates (>= {max_candidates}), stopping pagination")
                    break
                
                # Prepare for next page
                offset += limit
            
            print(f"   📊 Total candidates found: {len(all_candidates)}")
            
            if not all_candidates:
                print(f"❌ PRIMARY DISCOVERY FAILED: No candidates found for prefix: {slug_prefix}")
                return None
            
            # Filter by LIVE NOW with timezone-aware UTC
            now = datetime.now(timezone.utc)
            live_markets = []
            unknown_time_count = 0
            future_count = 0
            past_count = 0
            
            for candidate in all_candidates:
                is_live, status = self._is_candidate_live_now(candidate, now)
                
                if is_live:
                    live_markets.append(candidate)
                elif status == 'unknown_time':
                    unknown_time_count += 1
                elif status == 'future':
                    future_count += 1
                elif status == 'past':
                    past_count += 1
            
            print(f"   📊 LIVE NOW: {len(live_markets)} (unknown_time excluded: {unknown_time_count}; future excluded: {future_count}; past excluded: {past_count})")
            
            if not live_markets:
                print(f"❌ PRIMARY DISCOVERY FAILED: No LIVE NOW markets found")
                print(f"   - All {len(all_candidates)} candidates are future, past, or have unknown times")
                return None
            
            # Select the best candidate: closest end time (most current round)
            selected = self._select_best_live_market(live_markets, now)
            
            if not selected:
                print(f"❌ PRIMARY DISCOVERY FAILED: Could not select best market")
                return None
            
            # Log selection details
            slug = selected.get('slug')
            start_str = self._format_candidate_time(selected, 'start')
            end_str = self._format_candidate_time(selected, 'end')
            
            print(f"✅ PRIMARY DISCOVERY SUCCESS!")
            print(f"   Selected: slug={slug}")
            print(f"   Start: {start_str}")
            print(f"   End: {end_str}")
            print(f"   Reason: LIVE NOW market with closest end time (among {len(live_markets)} live options)")
            
            return selected
            
        except requests.RequestException as e:
            print(f"❌ PRIMARY DISCOVERY ERROR: Failed to fetch from Gamma /events API: {e}")
            return None
        except Exception as e:
            print(f"❌ PRIMARY DISCOVERY ERROR: Unexpected error: {e}")
            traceback.print_exc()
            return None
    
    def _extract_candidates_from_events(
        self,
        events: List[Dict[str, Any]],
        slug_prefix: str
    ) -> List[Dict[str, Any]]:
        """Extract market candidates from events matching slug prefix.
        
        Args:
            events: List of event dictionaries from API
            slug_prefix: Market slug prefix to match
        
        Returns:
            List of candidate dictionaries with normalized structure
        """
        candidates = []
        
        for event in events:
            # Check event slug
            event_slug = event.get('slug', '')
            if event_slug.startswith(slug_prefix):
                # Event itself is a match
                candidates.append({
                    'slug': event_slug,
                    'id': event.get('id'),
                    'question': event.get('question') or event.get('title', 'N/A'),
                    'start': event.get('startDate') or event.get('startTimestamp'),
                    'end': event.get('endDate') or event.get('endTimestamp'),
                    'source_type': 'event',
                    'raw': event
                })
            
            # Check markets within event
            markets = event.get('markets', [])
            if isinstance(markets, list):
                for market in markets:
                    market_slug = market.get('slug', '')
                    if market_slug.startswith(slug_prefix):
                        # Market is a match
                        candidates.append({
                            'slug': market_slug,
                            'id': market.get('id') or event.get('id'),
                            'question': market.get('question') or event.get('question', 'N/A'),
                            'start': market.get('startDate') or event.get('startDate'),
                            'end': market.get('endDate') or event.get('endDate'),
                            'source_type': 'market',
                            'raw': market
                        })
            
            # Check tickers/slugs arrays if present
            tickers = event.get('tickers', []) or event.get('slugs', [])
            if isinstance(tickers, list):
                for ticker in tickers:
                    if isinstance(ticker, str) and ticker.startswith(slug_prefix):
                        # Ticker is a match
                        candidates.append({
                            'slug': ticker,
                            'id': event.get('id'),
                            'question': event.get('question', 'N/A'),
                            'start': event.get('startDate'),
                            'end': event.get('endDate'),
                            'source_type': 'ticker',
                            'raw': event
                        })
        
        return candidates
    
    def _is_candidate_live_now(
        self,
        candidate: Dict[str, Any],
        now: datetime
    ) -> Tuple[bool, str]:
        """Check if candidate is LIVE NOW with timezone-aware UTC comparison.
        
        Args:
            candidate: Candidate dictionary
            now: Current UTC datetime (timezone-aware)
        
        Returns:
            Tuple of (is_live: bool, status: str)
            Status can be: 'live', 'future', 'past', 'unknown_time'
        """
        try:
            start_dt = self._parse_candidate_datetime(candidate, 'start')
            end_dt = self._parse_candidate_datetime(candidate, 'end')
            
            # If we can't parse times, mark as unknown_time (not live)
            if start_dt is None or end_dt is None:
                return False, 'unknown_time'
            
            # Ensure timezone-aware comparison
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            
            # Check if unreliable (e.g., full day duration suggests event-level times, not market-level)
            duration = (end_dt - start_dt).total_seconds()
            if duration >= 86400:  # 24 hours or more
                # Likely unreliable event-level times, not specific market times
                return False, 'unknown_time'
            
            # LIVE NOW check: start <= now < end
            if start_dt <= now < end_dt:
                return True, 'live'
            elif now < start_dt:
                return False, 'future'
            else:
                return False, 'past'
                
        except Exception as e:
            return False, 'unknown_time'
    
    def _parse_candidate_datetime(
        self,
        candidate: Dict[str, Any],
        time_type: str
    ) -> Optional[datetime]:
        """Parse start or end datetime from candidate data.
        
        Args:
            candidate: Candidate dictionary
            time_type: 'start' or 'end'
        
        Returns:
            Parsed datetime (timezone-aware UTC) or None if not available
        """
        try:
            # Get the time value from candidate
            time_val = candidate.get(time_type)
            
            if time_val is None:
                return None
            
            # Try parsing as ISO string
            if isinstance(time_val, str):
                # ISO format with Z: "2026-01-20T14:30:00Z"
                try:
                    if 'T' in time_val:
                        # Remove 'Z' and add timezone
                        dt = datetime.fromisoformat(time_val.replace('Z', '+00:00'))
                        # Ensure UTC
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                except ValueError:
                    pass
                
                # Try parsing as Unix timestamp string
                try:
                    ts = float(time_val)
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
                except (ValueError, OSError, OverflowError):
                    pass
            
            # Try parsing as Unix timestamp (int/float)
            elif isinstance(time_val, (int, float)):
                return datetime.fromtimestamp(time_val, tz=timezone.utc)
            
            return None
            
        except Exception:
            return None
    
    def _select_best_live_market(
        self,
        live_markets: List[Dict[str, Any]],
        now: datetime
    ) -> Optional[Dict[str, Any]]:
        """Select the best LIVE market (closest end time = most current round).
        
        Args:
            live_markets: List of LIVE market candidates
            now: Current UTC datetime
        
        Returns:
            Best market candidate or None
        """
        if not live_markets:
            return None
        
        # Sort by end time (earliest end time = most current round)
        def sort_key(candidate):
            end_dt = self._parse_candidate_datetime(candidate, 'end')
            if end_dt is None:
                return datetime.max.replace(tzinfo=timezone.utc)
            return end_dt
        
        sorted_markets = sorted(live_markets, key=sort_key)
        
        # Return the one with earliest end time (most current)
        return sorted_markets[0]
    
    def _format_candidate_time(
        self,
        candidate: Dict[str, Any],
        time_type: str
    ) -> Optional[str]:
        """Format start or end time for display.
        
        Args:
            candidate: Candidate dictionary
            time_type: 'start' or 'end'
        
        Returns:
            Formatted time string or None
        """
        dt = self._parse_candidate_datetime(candidate, time_type)
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        return None
    
    def find_active_market(self, slug_prefix: str) -> Optional[Dict[str, Any]]:
        """Find the most recent active market matching slug prefix (LEGACY fallback).
        
        This method uses the old /markets endpoint as a last resort.
        Uses enhanced Gamma API query with proper ordering to find fresh 15m events.
        Filters out future markets by checking startDate/endDate to only select live markets.
        
        Args:
            slug_prefix: Market slug prefix (e.g., "btc-updown-15m-")
        
        Returns:
            Market data dictionary or None if not found
        """
        try:
            print(f"🔍 LEGACY FALLBACK: Searching Gamma /markets API for prefix: {slug_prefix}")
            
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
            print(f"   📊 Gamma /markets API returned {len(markets)} total markets")
            
            # Filter markets by slug prefix
            matching = [
                m for m in markets 
                if m.get('slug', '').startswith(slug_prefix)
            ]
            
            print(f"   📊 Found {len(matching)} markets matching prefix '{slug_prefix}'")
            
            if not matching:
                print(f"❌ LEGACY FALLBACK FAILED: No active markets found for prefix: {slug_prefix}")
                return None
            
            # Filter by time: only keep markets that are LIVE NOW (start <= now < end)
            now = datetime.now(timezone.utc)
            live_markets = []
            
            for market in matching:
                is_live = self._is_market_live(market, now)
                if is_live:
                    live_markets.append(market)
            
            print(f"   📊 After LIVE NOW filter: {len(live_markets)} markets (filtered out {len(matching) - len(live_markets)} future/past markets)")
            
            if not live_markets:
                print(f"❌ LEGACY FALLBACK FAILED: No LIVE markets found (all {len(matching)} candidates are future or past markets)")
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
            
            print(f"✅ LEGACY FALLBACK SUCCESS!")
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
            print(f"❌ LEGACY FALLBACK ERROR: Failed to fetch from Gamma /markets API: {e}")
            return None
        except Exception as e:
            print(f"❌ LEGACY FALLBACK ERROR: Unexpected error: {e}")
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
            now: Current UTC datetime (timezone-aware)
        
        Returns:
            True if market is live now, False otherwise
        """
        try:
            # Parse start time from market data
            # Fields can be: startDate, startTime, or combined timestamp fields
            start_dt = self._parse_market_datetime(market, 'start')
            end_dt = self._parse_market_datetime(market, 'end')
            
            # If we can't parse times, assume it's NOT live (fail-closed)
            if start_dt is None or end_dt is None:
                return False
            
            # Ensure timezone-aware
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            
            # Check if market is live: start <= now < end
            return start_dt <= now < end_dt
            
        except Exception as e:
            # If parsing fails, assume market is NOT live (fail-closed)
            return False
    
    def _parse_market_datetime(self, market: Dict[str, Any], time_type: str) -> Optional[datetime]:
        """Parse start or end datetime from market data.
        
        Args:
            market: Market dictionary from Gamma API
            time_type: 'start' or 'end'
        
        Returns:
            Parsed datetime (timezone-aware UTC) or None if not available
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
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        # Ensure timezone-aware UTC
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                    except ValueError:
                        pass
                    # Try parsing as Unix timestamp string
                    try:
                        return datetime.fromtimestamp(float(date_str), tz=timezone.utc)
                    except (ValueError, OSError, OverflowError):
                        pass
                elif isinstance(date_str, (int, float)):
                    # Unix timestamp
                    return datetime.fromtimestamp(date_str, tz=timezone.utc)
            
            # Pattern 2: Separate date and time fields (startDate + startTime)
            date_field = f"{time_type}Date"
            time_field = f"{time_type}Time"
            if date_field in market and time_field in market:
                date_val = market[date_field]
                time_val = market[time_field]
                if date_val and time_val:
                    # Combine date and time strings
                    datetime_str = f"{date_val} {time_val}"
                    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                    # Ensure timezone-aware UTC
                    return dt.replace(tzinfo=timezone.utc)
            
            # Pattern 3: Single timestamp field (e.g., "startTimestamp")
            timestamp_field = f"{time_type}Timestamp"
            if timestamp_field in market and market[timestamp_field]:
                ts = market[timestamp_field]
                if isinstance(ts, (int, float)):
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
                elif isinstance(ts, str):
                    try:
                        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
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
        
        Only used when events API fails. Searches for visible text matching asset and time.
        
        Args:
            asset: Asset name ('BTC' or 'ETH')
            page: Playwright Page object (playwright.sync_api.Page)
            base_url: Polymarket base URL
            page_load_delay: Seconds to wait after page load (default: 2)
        
        Returns:
            Dictionary with event info or None if failed
        """
        try:
            print(f"\n🔍 FALLBACK DISCOVERY: Scraping UI for {asset} 15m event...")
            
            # Navigate to the 15m crypto aggregator page
            crypto_15m_url = f"{base_url}/crypto/15m"
            print(f"   📍 Navigating to: {crypto_15m_url}")
            # Use domcontentloaded instead of networkidle because Polymarket has live websockets
            page.goto(crypto_15m_url, wait_until='domcontentloaded', timeout=90000)
            
            # Wait for page to stabilize
            page.wait_for_timeout(1500)
            
            # Wait for page to fully load (allow dynamic content to render)
            time.sleep(page_load_delay)
            
            # Asset-specific search terms (case-insensitive)
            # Look for "[Asset] Up or Down" + "15 minute"
            asset_searches = {
                'BTC': ['Bitcoin Up or Down', 'Bitcoin Up or down'],
                'ETH': ['Ethereum Up or Down', 'Ethereum Up or down']
            }
            
            search_terms = asset_searches.get(asset.upper(), [f'{asset} Up or Down'])
            time_indicator = '15 minute'  # Look for "15 minute" text
            
            print(f"   🔍 Looking for {asset} event card with text: '{search_terms[0]}' and '{time_indicator}'...")
            
            event_href = None
            
            # Try to find event link by text content
            links_locator = page.locator('a[href*="/event/"]')
            link_count = links_locator.count()
            
            print(f"   📊 Found {link_count} total event links on page")
            
            # Collect all visible card titles for diagnostics
            all_card_titles = []
            
            for i in range(link_count):
                try:
                    link = links_locator.nth(i)
                    # Get the href
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Get the text content of the card (case-insensitive search)
                    try:
                        text_content = link.text_content() or ''
                        text_lower = text_content.lower()
                        
                        # Collect for diagnostics
                        if text_content.strip():
                            all_card_titles.append(text_content.strip()[:100])  # First 100 chars
                        
                        # Check if this card matches our asset
                        asset_match = any(term.lower() in text_lower for term in search_terms)
                        time_match = time_indicator.lower() in text_lower
                        
                        if asset_match and time_match:
                            # Also check slug pattern for confirmation
                            slug_pattern = f"{asset.lower()}-updown-15m-"
                            if slug_pattern in href:
                                event_href = href
                                print(f"   ✅ Found {asset} event link by text search: {href}")
                                break
                    except Exception:
                        pass
                        
                except Exception:
                    continue
            
            if not event_href:
                print(f"❌ FALLBACK DISCOVERY FAILED: Could not find {asset} event on {crypto_15m_url}")
                print(f"\n   🔍 DIAGNOSTIC: First 10 card titles found on page:")
                for idx, title in enumerate(all_card_titles[:10], 1):
                    print(f"      {idx}. {title}")
                if len(all_card_titles) == 0:
                    print(f"      (No card titles found - page may not have loaded correctly)")
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
    
    def get_market_details_with_tokens(
        self,
        slug: Optional[str] = None,
        market_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed market information including token IDs for Up/Down outcomes.
        
        This is the official method per Polymarket "Placing Your First Order" documentation:
        "First, get a token ID from the Gamma API"
        
        Args:
            slug: Market slug (e.g., "btc-updown-15m-jan20-1430")
            market_id: Market ID (alternative to slug)
        
        Returns:
            Dictionary with market details including:
            - market_slug: str
            - market_id: str
            - question: str
            - tokens: Dict with 'UP' and 'DOWN' token IDs
            or None if not found
        """
        try:
            print(f"\n🔍 Fetching market details from Gamma API...")
            
            if not slug and not market_id:
                print("❌ Either slug or market_id must be provided")
                return None
            
            # Try to fetch market by slug first
            if slug:
                print(f"   Looking for market by slug: {slug}")
                
                # Query markets endpoint with slug filter
                response = requests.get(
                    self.markets_url,
                    params={"slug": slug},
                    timeout=10
                )
                response.raise_for_status()
                markets = response.json()
                
                if not markets or len(markets) == 0:
                    print(f"❌ No market found with slug: {slug}")
                    return None
                
                market = markets[0]
                
            elif market_id:
                print(f"   Looking for market by ID: {market_id}")
                
                # Fetch specific market by ID
                market_url = f"{self.markets_url}/{market_id}"
                response = requests.get(market_url, timeout=10)
                response.raise_for_status()
                market = response.json()
            
            # Extract market details
            market_slug = market.get('slug', 'N/A')
            market_id_val = market.get('id', 'N/A')
            question = market.get('question', 'N/A')
            
            # Extract token IDs for Up/Down outcomes
            # Per Polymarket docs: markets have "tokens" or "outcomes" with tokenIds
            tokens = {}
            
            # Strategy 1: Look for 'tokens' array (most common)
            if 'tokens' in market and isinstance(market['tokens'], list):
                tokens_array = market['tokens']
                
                # Tokens array usually has 2 elements: [outcome1, outcome2]
                # For binary markets: typically ["Yes", "No"] or [0, 1]
                # For Up/Down: typically ["Up", "Down"] or similar
                
                if len(tokens_array) >= 2:
                    # For Up/Down markets, first token is typically UP (Yes/win)
                    # Second token is typically DOWN (No/lose)
                    # But we need to verify by checking outcome names if available
                    
                    # Try to find token IDs with outcome labels
                    up_token = None
                    down_token = None
                    
                    # Check if tokens have outcome property
                    for token in tokens_array:
                        if isinstance(token, dict):
                            token_id = token.get('token_id') or token.get('tokenId') or token.get('id')
                            outcome = token.get('outcome', '').lower()
                            
                            if 'yes' in outcome or 'up' in outcome or outcome == '1':
                                up_token = token_id
                            elif 'no' in outcome or 'down' in outcome or outcome == '0':
                                down_token = token_id
                        elif isinstance(token, str):
                            # Token is just a string ID
                            if up_token is None:
                                up_token = token
                            else:
                                down_token = token
                    
                    # If we found labeled tokens, use them
                    if up_token and down_token:
                        tokens['UP'] = up_token
                        tokens['DOWN'] = down_token
                    else:
                        # Fallback: assume first is UP, second is DOWN
                        tokens['UP'] = tokens_array[0] if isinstance(tokens_array[0], str) else tokens_array[0].get('token_id') or tokens_array[0].get('tokenId')
                        tokens['DOWN'] = tokens_array[1] if isinstance(tokens_array[1], str) else tokens_array[1].get('token_id') or tokens_array[1].get('tokenId')
            
            # Strategy 2: Look for 'outcomes' array (alternative structure)
            elif 'outcomes' in market and isinstance(market['outcomes'], list):
                outcomes = market['outcomes']
                
                for outcome in outcomes:
                    if isinstance(outcome, dict):
                        token_id = outcome.get('token_id') or outcome.get('tokenId') or outcome.get('id')
                        outcome_name = outcome.get('name', '').lower()
                        
                        if 'yes' in outcome_name or 'up' in outcome_name:
                            tokens['UP'] = token_id
                        elif 'no' in outcome_name or 'down' in outcome_name:
                            tokens['DOWN'] = token_id
            
            # Strategy 3: Look for conditionId (CLOB requirement)
            # Per docs: "conditionId" is the key identifier for CLOB trading
            condition_id = market.get('conditionId') or market.get('condition_id')
            
            if not tokens and condition_id:
                print(f"   ⚠️  No tokens array found, but found conditionId: {condition_id}")
                # In some cases, conditionId is used directly
                # We can't determine UP/DOWN without more info, but log it
            
            # Validate we found tokens
            if not tokens or 'UP' not in tokens or 'DOWN' not in tokens:
                print(f"⚠️  Warning: Could not extract UP/DOWN token IDs from market data")
                print(f"   Market structure: {list(market.keys())}")
                if 'tokens' in market:
                    print(f"   Tokens field: {market['tokens']}")
                if 'outcomes' in market:
                    print(f"   Outcomes field: {market['outcomes']}")
                if condition_id:
                    print(f"   ConditionId: {condition_id}")
                    # Return with conditionId even if we don't have individual token IDs
                    tokens['CONDITION_ID'] = condition_id
            
            result = {
                'market_slug': market_slug,
                'market_id': market_id_val,
                'question': question,
                'tokens': tokens,
                'condition_id': condition_id,
                'raw_market': market  # For debugging
            }
            
            print(f"✅ Market details fetched:")
            print(f"   Slug: {market_slug}")
            print(f"   Market ID: {market_id_val}")
            print(f"   Question: {question}")
            if tokens:
                if 'UP' in tokens:
                    print(f"   UP Token ID: {tokens['UP']}")
                if 'DOWN' in tokens:
                    print(f"   DOWN Token ID: {tokens['DOWN']}")
                if 'CONDITION_ID' in tokens:
                    print(f"   Condition ID: {tokens['CONDITION_ID']}")
            
            return result
            
        except requests.RequestException as e:
            print(f"❌ Failed to fetch market details from Gamma API: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error fetching market details: {e}")
            traceback.print_exc()
            return None
    
    def discover_15m_market(
        self,
        asset: str,
        slug_prefix: str,
        page=None,  # Optional Playwright Page for UI scraping
        base_url: str = "https://polymarket.com"
    ) -> Optional[Dict[str, Any]]:
        """Two-level discovery for 15m crypto markets.
        
        LEVEL 1 (Primary): Official Gamma /events API with LIVE NOW filtering
        LEVEL 2 (Fallback): UI scraping from polymarket.com/crypto/15m (when events API fails)
        
        Args:
            asset: Asset name ('BTC' or 'ETH')
            slug_prefix: Market slug prefix (e.g., "btc-updown-15m-")
            page: Optional Playwright Page object for UI scraping
            base_url: Polymarket base URL
        
        Returns:
            Dictionary with market/event info, or None if both methods fail
        """
        print("\n" + "="*70)
        print(f"🔍 TWO-LEVEL DISCOVERY FOR {asset.upper()} 15m MARKET")
        print("="*70)
        
        # LEVEL 1: Try official /events API first (Primary)
        print("\n🌐 LEVEL 1: Official Gamma /events API Discovery (Primary)")
        print("-" * 70)
        
        event_info = self.discover_15m_event_via_events_api(slug_prefix)
        
        if event_info:
            # Success with events API
            slug = event_info.get('slug')
            full_url = self.get_market_url(slug, base_url)
            
            result = {
                'slug': slug,
                'url': full_url,
                'asset': asset.upper(),
                'timestamp': self._extract_timestamp_from_slug(slug),
                'source': 'EVENTS_PRIMARY',
                'event_data': event_info
            }
            
            print("\n✅ Discovery complete via Official /events API (Primary)")
            print("="*70 + "\n")
            return result
        
        # LEVEL 2: Fallback to UI scraping
        print("\n🔄 LEVEL 2: UI Discovery (Fallback)")
        print("-" * 70)
        print("⚠️  Official /events API discovery did not succeed.")
        print("   This can happen when:")
        print("   - No LIVE NOW markets found (future markets scheduled but not started)")
        print("   - API indexing delay for new rounds")
        print("   - Network issues with Gamma API")
        print("\n   Attempting UI scraping fallback...")
        
        if not page:
            print("❌ No browser page provided for UI scraping")
            print("   UI fallback unavailable - both discovery methods failed")
            print("\n❌ DISCOVERY FAILED: Both /events API and UI scraping unavailable")
            print("="*70 + "\n")
            return None
        
        ui_event_info = self.discover_15m_event_via_ui(asset, page, base_url)
        
        if ui_event_info:
            print("\n✅ Discovery complete via UI (Fallback)")
            print("="*70 + "\n")
            return ui_event_info
        
        # Both methods failed
        print("\n❌ DISCOVERY FAILED: Both /events API and UI scraping failed")
        print("="*70 + "\n")
        return None
