"""
RTDS WebSocket client for real-time Chainlink price feeds.
"""

import asyncio
import json
import websockets
from datetime import datetime
from typing import Callable, Optional, Dict, Any
import threading
import queue


class RTDSClient:
    """WebSocket client for Polymarket RTDS (Real-Time Data Service)."""
    
    def __init__(self, ws_url: str, symbol: str):
        """
        Args:
            ws_url: WebSocket URL (e.g., wss://ws-live-data.polymarket.com)
            symbol: Trading symbol (e.g., "btc/usd" or "eth/usd")
        """
        self.ws_url = ws_url
        self.symbol = symbol.lower()
        self.price_queue = queue.Queue()
        self.running = False
        self.thread = None
        self._loop = None
        self._ws = None
    
    def start(self):
        """Start WebSocket client in background thread."""
        if self.running:
            print("⚠️  RTDS client already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        print(f"🌐 RTDS client started for {self.symbol}")
    
    def _run_async_loop(self):
        """Run async event loop in thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._connect())
        except Exception as e:
            print(f"❌ RTDS client error: {e}")
        finally:
            self._loop.close()
    
    async def _connect(self):
        """Connect to WebSocket and subscribe to price feed."""
        retry_count = 0
        max_retries = 5
        
        while self.running and retry_count < max_retries:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self._ws = ws
                    print(f"✅ Connected to RTDS WebSocket")
                    
                    # Subscribe to Chainlink crypto prices
                    subscribe_msg = {
                        "action": "subscribe",
                        "topic": "crypto_prices_chainlink",
                        "filters": {
                            "symbol": self.symbol
                        }
                    }
                    
                    await ws.send(json.dumps(subscribe_msg))
                    print(f"📡 Subscribed to topic: crypto_prices_chainlink, symbol: {self.symbol}")
                    
                    retry_count = 0  # Reset on successful connection
                    
                    # Listen for messages
                    async for message in ws:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self._handle_message(data)
                        except json.JSONDecodeError:
                            print(f"⚠️  Invalid JSON received: {message}")
                        except Exception as e:
                            print(f"⚠️  Error handling message: {e}")
            
            except websockets.exceptions.WebSocketException as e:
                retry_count += 1
                print(f"❌ WebSocket error: {e}")
                if retry_count < max_retries and self.running:
                    wait_time = min(2 ** retry_count, 30)
                    print(f"🔄 Retrying in {wait_time}s... ({retry_count}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Max retries reached, giving up")
                    break
            
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                break
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Process incoming WebSocket message.
        
        Args:
            data: Parsed JSON message
        """
        # Expected format:
        # {
        #   "topic": "crypto_prices_chainlink",
        #   "data": {
        #     "symbol": "btc/usd",
        #     "price": "43250.50",
        #     "timestamp": "2024-01-20T14:30:00Z"
        #   }
        # }
        
        if data.get('topic') == 'crypto_prices_chainlink':
            payload = data.get('data', {})
            symbol = payload.get('symbol', '').lower()
            
            if symbol == self.symbol:
                try:
                    price = float(payload.get('price', 0))
                    timestamp_str = payload.get('timestamp')
                    
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.utcnow()
                    
                    tick = {
                        'price': price,
                        'timestamp': timestamp,
                        'symbol': symbol
                    }
                    
                    self.price_queue.put(tick)
                    
                except (ValueError, TypeError) as e:
                    print(f"⚠️  Error parsing price data: {e}")
    
    def get_latest_price(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Get latest price tick from queue.
        
        Args:
            timeout: Max seconds to wait for price
        
        Returns:
            Price tick dict or None if timeout
        """
        try:
            return self.price_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_prices(self) -> list:
        """Get all pending price ticks from queue.
        
        Returns:
            List of price tick dicts
        """
        prices = []
        while not self.price_queue.empty():
            try:
                prices.append(self.price_queue.get_nowait())
            except queue.Empty:
                break
        return prices
    
    def stop(self):
        """Stop WebSocket client."""
        if not self.running:
            return
        
        print("🛑 Stopping RTDS client...")
        self.running = False
        
        if self._ws:
            # Schedule close in the event loop
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("✅ RTDS client stopped")
