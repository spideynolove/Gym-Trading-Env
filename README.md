
<h1 align='center'>
   <img src = 'https://github.com/ClementPerroud/Gym-Trading-Env/raw/main/docs/source/images/logo_light-bg.png' width='500'>
</h1>

<section class="shields" align="center">
   <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-v3-brightgreen.svg"
         alt="python">
   </a>
   <a href="https://pypi.org/project/gym-trading-env/">
      <img src="https://img.shields.io/badge/pypi-v1.1.3-brightgreen.svg"
         alt="PyPI">
   </a>
   <a href="https://github.com/ClementPerroud/Gym-Trading-Env/blob/main/LICENSE.txt">
   <img src="https://img.shields.io/badge/license-MIT%202.0%20Clause-green"
         alt="Apache 2.0 with Commons Clause">
   </a>
   <a href='https://gym-trading-env.readthedocs.io/en/latest/?badge=latest'>
         <img src='https://readthedocs.org/projects/gym-trading-env/badge/?version=latest' alt='Documentation Status' />
   </a>
   <a href="https://github.com/ClementPerroud/Gym-Trading-Env">
      <img src="https://img.shields.io/github/stars/ClementPerroud/gym-trading-env?style=social" alt="Github stars">
   </a>
</section>
  
Gym Trading Env is an advanced Gymnasium environment for simulating forex markets and training Reinforcement Learning (RL) trading agents with comprehensive intermarket analysis capabilities.
It was designed to be fast, customizable, and feature-rich for professional-grade RL trading algorithms implementation.


| [Documentation](https://gym-trading-env.readthedocs.io/en/latest/index.html) |


Key Features
---------------

This enhanced package provides professional-grade forex trading simulation with advanced intermarket analysis:

### 🚀 **Core Trading Environment**
* **Multi-Asset Support**: Forex, Commodities, Bonds, and Equities coordination
* **Enhanced Position Sizing**: 7-factor risk management system
* **Real-Time Data Integration**: Economic calendar and news event processing
* **Session-Aware Trading**: Liquidity and volatility-based position adjustments

### 🧠 **Advanced ML/RL Features**
* **18 Enhanced Observation Features**: Including FA+TA+IA framework signals
* **Multi-Dataset Coordination**: Automatic dataset switching with intermarket analysis
* **Sophisticated Risk Management**: Correlation-adjusted position sizing
* **Real Economic Data**: Integration with news events and economic indicators

### 🌐 **Intermarket Analysis Capabilities**
* **Murphy's 5 Intermarket Principles**: Automated detection and signals
* **Cross-Market Confirmations**: Multi-asset correlation analysis
* **Trading Scenario Engine**: 9 specific market condition detectors
* **Currency Strength Analysis**: Real-time relative strength calculations

### 📊 **Professional Features**
* **High Performance Rendering**: Display hundreds of thousands of candles simultaneously
* **Complex Trading Operations**: Short selling, margin trading, correlation management
* **Production-Ready**: Comprehensive error handling and fallback mechanisms
* **Extensible Architecture**: Easy integration of custom analysis components 

![Render animated image](https://raw.githubusercontent.com/ClementPerroud/Gym-Trading-Env/main/docs/source/images/render.gif)

Installation
---------------

Gym Trading Env supports Python 3.9+ on Windows, Mac, and Linux. 

### Standard Installation
```bash
pip install gym-trading-env
```

### Enhanced Version (This Repository)
```bash
git clone https://github.com/spideynolove/Gym-Trading-Env
cd Gym-Trading-Env
pip install -e .
```

Quick Start
-----------

### Basic Enhanced Trading Environment
```python
import gymnasium as gym
import gym_trading_env

# Create enhanced forex environment
env = gym.make('TradingEnv',
    df=your_forex_data,
    enable_enhanced_features=True,
    currency_pair="EUR/USD"
)

obs, info = env.reset()
# obs now contains 18 enhanced features including FA+TA+IA signals
```

### Multi-Asset Intermarket Analysis
```python
# Multi-dataset environment with intermarket analysis
env = gym.make('MultiDatasetTradingEnv',
    dataset_dir='data/forex/*.pkl',
    enable_enhanced_features=True,
    base_data_dir='data',  # Contains forex/, commodities/, bonds/, equities/
    episodes_between_dataset_switch=5
)

# Environment automatically coordinates across:
# - Forex pairs (8 major pairs)
# - Commodities (Gold, Oil, CRB Index)  
# - Bonds (6 major government bonds)
# - Equities (6 major indices)
```

### Enhanced Features Overview
```python
# 18 Enhanced observation features:
obs[0:8]   # Original enhanced features (COT, news, session)
obs[9:16]  # FA+TA+IA framework features
obs[17]    # Murphy's intermarket principles score

# 7-factor position sizing considers:
# 1. Session timing (liquidity/volatility)
# 2. News events (economic calendar)  
# 3. Correlation exposure (portfolio risk)
# 4. Market conditions (COT + unified analysis)
# 5. FA+TA+IA signals (comprehensive analysis)
# 6. Intermarket principles (Murphy's principles)
# 7. Trading scenarios (specific market conditions)
```

Technical Architecture
---------------------

### Enhanced Components
- **FA+TA+IA Framework**: Fundamental + Technical + Intermarket analysis
- **Murphy Principles Detector**: Automated intermarket relationship detection
- **Trading Scenario Engine**: 9 specific market condition patterns
- **Cross-Market Analytics**: Multi-asset correlation and regime detection
- **Economic Calendar Integration**: Real-time news event processing

### Multi-Asset Coordination
- **IntermarketDatasetManager**: Synchronizes data across asset classes
- **Correlation Manager**: Dynamic correlation tracking and regime detection  
- **Session Manager**: Trading session liquidity and volatility analysis
- **News Risk Manager**: Economic event impact assessment

-----------------------------------------------------------------------------------------------

## 🎯 What's New in This Enhanced Version

### ✅ **Comprehensive Intermarket Analysis**
This enhanced version includes professional-grade intermarket analysis capabilities based on John Murphy's "Intermarket Analysis" methodology:

- **18 Enhanced Observation Features** for sophisticated ML/RL training
- **7-Factor Position Sizing** for advanced risk management
- **Real Economic Data Integration** from news calendars
- **Multi-Asset Coordination** across Forex, Commodities, Bonds, and Equities
- **Murphy's 5 Intermarket Principles** automated detection
- **Trading Scenario Engine** with 9 specific market patterns

### 🚀 **Production-Ready Features**
- Comprehensive error handling and fallback mechanisms
- Memory-optimized multi-dataset coordination
- Session-aware trading with liquidity considerations
- Real-time correlation regime detection
- Economic calendar event processing

Perfect for advanced forex trading research, institutional algorithm development, and sophisticated ML/RL applications.
