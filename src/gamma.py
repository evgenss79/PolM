"""
Gamma API client for discovering active Polymarket markets.
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class GammaAPI:
    """Client for Polymarket Gamma API to find active markets."""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def find_active_market(self, slug_prefix: str) -> Optional[Dict[str, Any]]:
        """Find the most recent active market matching slug prefix.
        
        Args:
            slug_prefix: Market slug prefix (e.g., "btc-updown-15m-")
        
        Returns:
            Market data dictionary or None if not found
        """
        try:
            print(f"🔍 Searching for markets with prefix: {slug_prefix}")
            
            # Query Gamma API
            response = requests.get(
                self.api_url,
                params={
                    "closed": "false",  # Only active markets
                    "limit": 100
                },
                timeout=10
            )
            response.raise_for_status()
            
            markets = response.json()
            
            # Filter markets by slug prefix
            matching = [
                m for m in markets 
                if m.get('slug', '').startswith(slug_prefix)
            ]
            
            if not matching:
                print(f"❌ No active markets found for prefix: {slug_prefix}")
                return None
            
            # Sort by most recent (newest first)
            # Markets have 'id' field which increases with time
            matching.sort(key=lambda x: x.get('id', 0), reverse=True)
            
            market = matching[0]
            slug = market.get('slug')
            question = market.get('question', 'N/A')
            
            print(f"✅ Found active market: {slug}")
            print(f"   Question: {question}")
            
            return market
            
        except requests.RequestException as e:
            print(f"❌ Error fetching markets from Gamma API: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error in market discovery: {e}")
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
