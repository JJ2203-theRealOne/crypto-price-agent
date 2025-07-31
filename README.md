# Crypto Trading Agent 🤖

An autonomous cryptocurrency monitoring agent that generates real-time trading signals based on price movements and market volatility.

## 🌟 Features

- **Autonomous Operation**: Runs continuously without human intervention
- **Real-time Monitoring**: Tracks cryptocurrency prices every 5 minutes
- **Smart Signal Generation**: 
  - SELL signals when prices drop significantly
  - BUY signals when prices surge
  - VOLATILITY alerts during high market fluctuation
- **Persistent State Management**: Remembers price history and signals between sessions
- **Configurable Thresholds**: Easy customization via JSON configuration
- **Performance Tracking**: Monitors agent uptime and signal generation metrics

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- `requests` library

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-trading-agent.git
cd crypto-trading-agent
