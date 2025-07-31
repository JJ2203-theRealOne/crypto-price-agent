import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class CryptoTradingAgent:
    """Autonomous cryptocurrency monitoring and trading signal agent"""
    
    def __init__(self, config_file='agent_config.json'):
        self.api_url = "https://api.coingecko.com/api/v3/simple/price"
        self.state_file = 'agent_state.json'
        self.config_file = config_file
        
        # Load configuration
        self.config = self.load_config()
        
        # Load persistent state
        self.state = self.load_state()
        
        # Initialize if first run
        if not self.state:
            self.state = {
                'previous_prices': {},
                'price_history': {},
                'signals_generated': [],
                'last_check': None,
                'total_alerts': 0,
                'agent_start_time': datetime.now().isoformat()
            }
    
    def load_config(self) -> dict:
        """Load agent configuration from file or use defaults"""
        default_config = {
            'coins': {
                'bitcoin': 'BTC',
                'ethereum': 'ETH', 
                'solana': 'SOL',
                'cardano': 'ADA',
                'polkadot': 'DOT'
            },
            'thresholds': {
                'drop_alert': -5.0,
                'surge_alert': 10.0,
                'volatility_window': 24  # hours
            },
            'check_interval': 300,  # 5 minutes
            'enable_surge_alerts': True,
            'enable_volatility_tracking': True,
            'max_history_length': 288  # 24 hours of 5-min intervals
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        
        return default_config
    
    def load_state(self) -> Optional[dict]:
        """Load persistent state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading state: {e}")
        return None
    
    def save_state(self):
        """Save current state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def get_current_prices(self) -> Optional[Dict[str, float]]:
        """Fetch current cryptocurrency prices"""
        try:
            params = {
                'ids': ','.join(self.config['coins'].keys()),
                'vs_currencies': 'usd'
            }
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current_prices = {}
            for coin_id, ticker in self.config['coins'].items():
                if coin_id in data:
                    current_prices[ticker] = data[coin_id]['usd']
            
            return current_prices
            
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return None
    
    def calculate_percentage_change(self, old_price: float, new_price: float) -> float:
        """Calculate percentage change between prices"""
        if old_price == 0:
            return 0
        return ((new_price - old_price) / old_price) * 100
    
    def update_price_history(self, current_prices: Dict[str, float]):
        """Update price history for volatility tracking"""
        timestamp = datetime.now().isoformat()
        
        for ticker, price in current_prices.items():
            if ticker not in self.state['price_history']:
                self.state['price_history'][ticker] = []
            
            self.state['price_history'][ticker].append({
                'price': price,
                'timestamp': timestamp
            })
            
            # Trim history to max length
            max_len = self.config['max_history_length']
            if len(self.state['price_history'][ticker]) > max_len:
                self.state['price_history'][ticker] = self.state['price_history'][ticker][-max_len:]
    
    def calculate_volatility(self, ticker: str) -> float:
        """Calculate price volatility over the configured window"""
        if ticker not in self.state['price_history'] or len(self.state['price_history'][ticker]) < 2:
            return 0
        
        prices = [entry['price'] for entry in self.state['price_history'][ticker]]
        avg_price = sum(prices) / len(prices)
        
        if avg_price == 0:
            return 0
        
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        volatility = (std_dev / avg_price) * 100
        
        return volatility
    
    def generate_trading_signals(self, current_prices: Dict[str, float]) -> List[dict]:
        """Generate trading signals based on multiple factors"""
        signals = []
        
        if not self.state['previous_prices']:
            return signals
        
        for ticker in current_prices:
            if ticker in self.state['previous_prices']:
                old_price = self.state['previous_prices'][ticker]
                new_price = current_prices[ticker]
                change = self.calculate_percentage_change(old_price, new_price)
                volatility = self.calculate_volatility(ticker)
                
                signal = None
                
                # Drop signal
                if change <= self.config['thresholds']['drop_alert']:
                    signal = {
                        'type': 'SELL_SIGNAL',
                        'coin': ticker,
                        'reason': f"Price dropped {change:.2f}%",
                        'old_price': old_price,
                        'new_price': new_price,
                        'change': change,
                        'volatility': volatility,
                        'timestamp': datetime.now().isoformat(),
                        'strength': 'STRONG' if change <= -10 else 'MODERATE'
                    }
                
                # Surge signal
                elif self.config['enable_surge_alerts'] and change >= self.config['thresholds']['surge_alert']:
                    signal = {
                        'type': 'BUY_SIGNAL',
                        'coin': ticker,
                        'reason': f"Price surged {change:.2f}%",
                        'old_price': old_price,
                        'new_price': new_price,
                        'change': change,
                        'volatility': volatility,
                        'timestamp': datetime.now().isoformat(),
                        'strength': 'STRONG' if change >= 20 else 'MODERATE'
                    }
                
                # High volatility signal
                elif self.config['enable_volatility_tracking'] and volatility > 15:
                    signal = {
                        'type': 'VOLATILITY_ALERT',
                        'coin': ticker,
                        'reason': f"High volatility detected: {volatility:.2f}%",
                        'old_price': old_price,
                        'new_price': new_price,
                        'change': change,
                        'volatility': volatility,
                        'timestamp': datetime.now().isoformat(),
                        'strength': 'WARNING'
                    }
                
                if signal:
                    signals.append(signal)
                    self.state['signals_generated'].append(signal)
                    self.state['total_alerts'] += 1
        
        return signals
    
    def display_status(self, current_prices: Dict[str, float]):
        """Display current market status"""
        print(f"\n{'='*60}")
        print(f"Agent Status: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Running since: {self.state['agent_start_time']}")
        print(f"Total signals generated: {self.state['total_alerts']}")
        print(f"{'='*60}")
        
        for ticker, price in current_prices.items():
            price_str = f"${price:,.2f}"
            
            if ticker in self.state['previous_prices']:
                old_price = self.state['previous_prices'][ticker]
                change = self.calculate_percentage_change(old_price, price)
                volatility = self.calculate_volatility(ticker)
                
                if change > 0:
                    change_str = f"UP +{change:.2f}%"
                elif change < 0:
                    change_str = f"DOWN {change:.2f}%"
                else:
                    change_str = "FLAT 0.00%"
                
                print(f"{ticker}: {price_str} {change_str} | Volatility: {volatility:.2f}%")
            else:
                print(f"{ticker}: {price_str} | Initializing...")
    
    def display_signals(self, signals: List[dict]):
        """Display generated trading signals"""
        if not signals:
            return
        
        print(f"\n{'!'*60}")
        print("TRADING SIGNALS GENERATED")
        print(f"{'!'*60}")
        
        for signal in signals:
            print(f"\n{signal['type']} - {signal['coin']}")
            print(f"Reason: {signal['reason']}")
            print(f"Price: ${signal['old_price']:,.2f} -> ${signal['new_price']:,.2f}")
            print(f"Volatility: {signal['volatility']:.2f}%")
            print(f"Signal Strength: {signal['strength']}")
            print(f"Time: {signal['timestamp']}")
        
        print(f"\n{'!'*60}")
    
    def get_agent_summary(self) -> dict:
        """Get summary of agent performance"""
        summary = {
            'uptime': str(datetime.now() - datetime.fromisoformat(self.state['agent_start_time'])),
            'total_signals': self.state['total_alerts'],
            'monitored_coins': len(self.config['coins']),
            'check_interval': f"{self.config['check_interval']} seconds",
            'last_check': self.state['last_check']
        }
        
        # Count signal types
        signal_types = {}
        for signal in self.state['signals_generated']:
            signal_type = signal['type']
            signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
        
        summary['signal_breakdown'] = signal_types
        return summary
    
    def run_agent(self):
        """Main autonomous agent loop"""
        print(">>> Crypto Trading Agent Starting...")
        print(f"Monitoring: {', '.join(self.config['coins'].values())}")
        print(f"Check interval: {self.config['check_interval']} seconds")
        print(f"Drop threshold: {self.config['thresholds']['drop_alert']}%")
        print(f"Surge threshold: {self.config['thresholds']['surge_alert']}%")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Fetch current prices
                current_prices = self.get_current_prices()
                
                if current_prices:
                    # Update price history
                    self.update_price_history(current_prices)
                    
                    # Generate trading signals
                    signals = self.generate_trading_signals(current_prices)
                    
                    # Display status
                    self.display_status(current_prices)
                    
                    # Display any new signals
                    if signals:
                        self.display_signals(signals)
                    
                    # Update state
                    self.state['previous_prices'] = current_prices.copy()
                    self.state['last_check'] = datetime.now().isoformat()
                    
                    # Save state to disk
                    self.save_state()
                    
                    # Show summary every 10 checks
                    if self.state['total_alerts'] % 10 == 0 and self.state['total_alerts'] > 0:
                        summary = self.get_agent_summary()
                        print(f"\n=== Agent Summary ===")
                        print(f"Uptime: {summary['uptime']}")
                        print(f"Signal breakdown: {summary['signal_breakdown']}")
                else:
                    print("WARNING: Failed to fetch prices, retrying...")
                
                # Wait for next check
                print(f"\nSleeping for {self.config['check_interval']} seconds...")
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            print("\n\n>>> Agent stopped by user")
            summary = self.get_agent_summary()
            print(f"\n=== Final Summary ===")
            print(f"Total runtime: {summary['uptime']}")
            print(f"Total signals generated: {summary['total_signals']}")
            print(f"Signal breakdown: {summary['signal_breakdown']}")
            
            # Save final state
            self.save_state()
            print("\n>>> State saved successfully")
            
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            self.save_state()


if __name__ == "__main__":
    # Create and run the agent
    agent = CryptoTradingAgent()
    agent.run_agent()