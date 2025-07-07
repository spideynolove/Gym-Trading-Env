import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import datetime
import pytz
from .intermarket_dataset_manager import IntermarketDatasetManager, AssetType

class CurrencyProfile(Enum):
    USD = "USD"
    EUR = "EUR" 
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"
    CAD = "CAD"
    NZD = "NZD"
    CHF = "CHF"

@dataclass
class EconomicIndicator:
    currency: CurrencyProfile
    indicator_name: str
    impact_level: str
    release_frequency: str
    expected_value: float
    actual_value: float
    previous_value: float
    timestamp: datetime.datetime

@dataclass
class MarketSentiment:
    sentiment_score: float
    confidence: float
    primary_drivers: List[str]
    risk_appetite: str
    timestamp: datetime.datetime

class FAAnalyzer:
    
    def __init__(self):
        self.currency_indicators = {
            CurrencyProfile.USD: ['NFP', 'CPI', 'Fed_Rate', 'GDP', 'Unemployment'],
            CurrencyProfile.EUR: ['CPI_Flash', 'ECB_Rate', 'GDP', 'Unemployment', 'PMI'],
            CurrencyProfile.GBP: ['BOE_Rate', 'CPI', 'GDP', 'Employment', 'PMI'],
            CurrencyProfile.JPY: ['BOJ_Rate', 'CPI', 'GDP', 'Tankan', 'Trade_Balance'],
            CurrencyProfile.AUD: ['RBA_Rate', 'CPI', 'Employment', 'Trade_Balance', 'China_PMI'],
            CurrencyProfile.CAD: ['BOC_Rate', 'CPI', 'Employment', 'Trade_Balance', 'Oil_Inventory'],
            CurrencyProfile.NZD: ['RBNZ_Rate', 'CPI', 'Employment', 'Trade_Balance', 'GDT_Index'],
            CurrencyProfile.CHF: ['SNB_Rate', 'CPI', 'GDP', 'Trade_Balance', 'Gold_Reserves']
        }
        self.sentiment_weights = {
            'monetary_policy': 0.3,
            'economic_growth': 0.25,
            'inflation': 0.2,
            'employment': 0.15,
            'trade_balance': 0.1
        }
    
    def analyze_currency_fundamentals(self, currency: CurrencyProfile, indicators: List[EconomicIndicator]):
        fa_score = 0.0
        indicator_scores = {}
        
        for indicator in indicators:
            if indicator.currency == currency:
                score = self.calculate_indicator_impact(indicator)
                indicator_scores[indicator.indicator_name] = score
                
                weight = self.get_indicator_weight(indicator.indicator_name)
                fa_score += score * weight
        
        return {
            'currency': currency.value,
            'fa_score': np.clip(fa_score, -1.0, 1.0),
            'indicator_scores': indicator_scores,
            'analysis_timestamp': datetime.datetime.now(pytz.UTC)
        }
    
    def calculate_indicator_impact(self, indicator: EconomicIndicator):
        if indicator.expected_value == 0:
            return 0.0
        
        surprise_factor = (indicator.actual_value - indicator.expected_value) / abs(indicator.expected_value)
        
        impact_multiplier = {
            'High': 1.0,
            'Medium': 0.6,
            'Low': 0.3
        }.get(indicator.impact_level, 0.5)
        
        return np.clip(surprise_factor * impact_multiplier, -1.0, 1.0)
    
    def get_indicator_weight(self, indicator_name: str):
        weight_mapping = {
            'NFP': 0.3, 'Fed_Rate': 0.3, 'ECB_Rate': 0.3, 'BOE_Rate': 0.3,
            'CPI': 0.25, 'CPI_Flash': 0.25,
            'GDP': 0.2, 'Employment': 0.15, 'Unemployment': 0.15,
            'Trade_Balance': 0.1, 'PMI': 0.15,
            'GDT_Index': 0.2, 'Oil_Inventory': 0.15
        }
        return weight_mapping.get(indicator_name, 0.1)
    
    def determine_market_sentiment(self, currency_scores: Dict[str, float], intermarket_data: Dict):
        sentiment_factors = []
        
        # Currency strength analysis
        usd_score = currency_scores.get('USD', 0.0)
        if abs(usd_score) > 0.3:
            sentiment_factors.append(f"USD {'strength' if usd_score > 0 else 'weakness'}")
        
        # Risk appetite from equity markets
        if 'equities_SPX' in intermarket_data:
            spx_change = intermarket_data['equities_SPX'].pct_change().iloc[-1]
            if spx_change > 0.01:
                sentiment_factors.append("Risk-on sentiment")
            elif spx_change < -0.01:
                sentiment_factors.append("Risk-off sentiment")
        
        # Safe-haven demand
        if 'commodities_XAUUSD' in intermarket_data and 'forex_USDJPY' in intermarket_data:
            gold_change = intermarket_data['commodities_XAUUSD'].pct_change().iloc[-1]
            jpy_change = intermarket_data['forex_USDJPY'].pct_change().iloc[-1]
            
            if gold_change > 0.005 and jpy_change < -0.005:
                sentiment_factors.append("Safe-haven demand")
        
        overall_sentiment = np.mean([currency_scores.get(curr, 0.0) for curr in currency_scores])
        
        return MarketSentiment(
            sentiment_score=overall_sentiment,
            confidence=min(1.0, len(sentiment_factors) * 0.3),
            primary_drivers=sentiment_factors,
            risk_appetite="Risk-on" if overall_sentiment > 0.1 else "Risk-off" if overall_sentiment < -0.1 else "Neutral",
            timestamp=datetime.datetime.now(pytz.UTC)
        )

class TAAnalyzer:
    
    def __init__(self):
        self.candlestick_patterns = [
            'bullish_engulfing', 'bearish_engulfing', 'hammer', 'doji',
            'head_and_shoulders', 'rising_wedge', 'falling_wedge'
        ]
        self.chart_patterns = [
            'support_resistance', 'trend_lines', 'fibonacci_retracements'
        ]
    
    def analyze_technical_signals(self, data: pd.DataFrame, timeframe: str = '1H'):
        ta_signals = {}
        
        # Trend analysis
        ta_signals['trend'] = self.identify_trend(data)
        
        # Support/Resistance levels
        ta_signals['support_resistance'] = self.find_support_resistance(data)
        
        # Candlestick patterns
        ta_signals['candlestick_patterns'] = self.detect_candlestick_patterns(data)
        
        # Technical indicators
        ta_signals['rsi'] = self.calculate_rsi(data['close'])
        ta_signals['macd'] = self.calculate_macd(data['close'])
        ta_signals['bollinger_bands'] = self.calculate_bollinger_bands(data['close'])
        
        # Entry/Exit signals
        ta_signals['entry_signals'] = self.generate_entry_signals(ta_signals)
        ta_signals['exit_signals'] = self.generate_exit_signals(ta_signals)
        
        return ta_signals
    
    def identify_trend(self, data: pd.DataFrame, period: int = 20):
        if len(data) < period:
            return 'Neutral'
        
        recent_high = data['high'].rolling(period).max().iloc[-1]
        recent_low = data['low'].rolling(period).min().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        if current_price > recent_high * 0.95:
            return 'Uptrend'
        elif current_price < recent_low * 1.05:
            return 'Downtrend'
        else:
            return 'Sideways'
    
    def find_support_resistance(self, data: pd.DataFrame, window: int = 10):
        highs = data['high'].rolling(window=window, center=True).max()
        lows = data['low'].rolling(window=window, center=True).min()
        
        resistance_levels = data[data['high'] == highs]['high'].unique()
        support_levels = data[data['low'] == lows]['low'].unique()
        
        current_price = data['close'].iloc[-1]
        
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
        nearest_support = max([s for s in support_levels if s < current_price], default=None)
        
        return {
            'nearest_resistance': nearest_resistance,
            'nearest_support': nearest_support,
            'all_resistance': sorted(resistance_levels[resistance_levels > current_price])[:3],
            'all_support': sorted(support_levels[support_levels < current_price], reverse=True)[:3]
        }
    
    def detect_candlestick_patterns(self, data: pd.DataFrame):
        patterns = {}
        
        if len(data) < 3:
            return patterns
        
        last_candles = data.tail(3)
        
        # Bullish Engulfing
        if (last_candles.iloc[-2]['close'] < last_candles.iloc[-2]['open'] and
            last_candles.iloc[-1]['close'] > last_candles.iloc[-1]['open'] and
            last_candles.iloc[-1]['open'] < last_candles.iloc[-2]['close'] and
            last_candles.iloc[-1]['close'] > last_candles.iloc[-2]['open']):
            patterns['bullish_engulfing'] = True
        
        # Bearish Engulfing
        if (last_candles.iloc[-2]['close'] > last_candles.iloc[-2]['open'] and
            last_candles.iloc[-1]['close'] < last_candles.iloc[-1]['open'] and
            last_candles.iloc[-1]['open'] > last_candles.iloc[-2]['close'] and
            last_candles.iloc[-1]['close'] < last_candles.iloc[-2]['open']):
            patterns['bearish_engulfing'] = True
        
        # Hammer pattern
        last = last_candles.iloc[-1]
        body_size = abs(last['close'] - last['open'])
        lower_shadow = min(last['open'], last['close']) - last['low']
        upper_shadow = last['high'] - max(last['open'], last['close'])
        
        if lower_shadow > 2 * body_size and upper_shadow < body_size:
            patterns['hammer'] = True
        
        return patterns
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if len(rsi) > 0 else 50
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.iloc[-1] if len(macd_line) > 0 else 0,
            'signal': signal_line.iloc[-1] if len(signal_line) > 0 else 0,
            'histogram': histogram.iloc[-1] if len(histogram) > 0 else 0
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        rolling_mean = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        
        upper_band = rolling_mean + (rolling_std * std_dev)
        lower_band = rolling_mean - (rolling_std * std_dev)
        
        current_price = prices.iloc[-1]
        return {
            'upper': upper_band.iloc[-1] if len(upper_band) > 0 else current_price,
            'middle': rolling_mean.iloc[-1] if len(rolling_mean) > 0 else current_price,
            'lower': lower_band.iloc[-1] if len(lower_band) > 0 else current_price,
            'position': 'overbought' if current_price > upper_band.iloc[-1] else 'oversold' if current_price < lower_band.iloc[-1] else 'normal'
        }
    
    def generate_entry_signals(self, ta_signals: Dict):
        entry_signals = []
        
        # Trend + RSI signal
        if ta_signals['trend'] == 'Uptrend' and ta_signals.get('rsi', 50) < 30:
            entry_signals.append({'type': 'long', 'reason': 'oversold_in_uptrend', 'strength': 0.7})
        
        if ta_signals['trend'] == 'Downtrend' and ta_signals.get('rsi', 50) > 70:
            entry_signals.append({'type': 'short', 'reason': 'overbought_in_downtrend', 'strength': 0.7})
        
        # Candlestick pattern signals
        patterns = ta_signals.get('candlestick_patterns', {})
        if patterns.get('bullish_engulfing'):
            entry_signals.append({'type': 'long', 'reason': 'bullish_engulfing', 'strength': 0.6})
        
        if patterns.get('bearish_engulfing'):
            entry_signals.append({'type': 'short', 'reason': 'bearish_engulfing', 'strength': 0.6})
        
        return entry_signals
    
    def generate_exit_signals(self, ta_signals: Dict):
        exit_signals = []
        
        # RSI extreme readings
        rsi = ta_signals.get('rsi', 50)
        if rsi > 80:
            exit_signals.append({'type': 'exit_long', 'reason': 'overbought', 'urgency': 0.8})
        if rsi < 20:
            exit_signals.append({'type': 'exit_short', 'reason': 'oversold', 'urgency': 0.8})
        
        # Bollinger Band extremes
        bb = ta_signals.get('bollinger_bands', {})
        if bb.get('position') == 'overbought':
            exit_signals.append({'type': 'exit_long', 'reason': 'bollinger_overbought', 'urgency': 0.6})
        if bb.get('position') == 'oversold':
            exit_signals.append({'type': 'exit_short', 'reason': 'bollinger_oversold', 'urgency': 0.6})
        
        return exit_signals

class IAAnalyzer:
    
    def __init__(self, dataset_manager: IntermarketDatasetManager):
        self.dataset_manager = dataset_manager
        self.correlation_thresholds = {
            'strong_positive': 0.7,
            'moderate_positive': 0.4,
            'weak': 0.2,
            'moderate_negative': -0.4,
            'strong_negative': -0.7
        }
    
    def analyze_cross_market_signals(self, primary_asset: str, timestamp: datetime.datetime):
        ia_signals = {}
        
        # Get intermarket data
        intermarket_data = self.dataset_manager.synchronized_data
        if not intermarket_data:
            return ia_signals
        
        # Murphy's principles analysis
        ia_signals['murphy_principles'] = self.analyze_murphy_principles()
        
        # Cross-market confirmations
        ia_signals['confirmations'] = self.get_cross_market_confirmations(primary_asset)
        
        # Leading indicator signals
        ia_signals['leading_indicators'] = self.analyze_leading_indicators()
        
        # Risk sentiment analysis
        ia_signals['risk_sentiment'] = self.analyze_risk_sentiment()
        
        return ia_signals
    
    def analyze_murphy_principles(self):
        murphy_data = self.dataset_manager.get_murphy_principle_data()
        principles_signals = {}
        
        # Principle 1: Bonds vs Commodities inverse
        if 'bonds_commodities' in murphy_data:
            bonds = murphy_data['bonds_commodities']['bonds'].pct_change().tail(20)
            commodities = murphy_data['bonds_commodities']['commodities'].pct_change().tail(20)
            correlation = bonds.corr(commodities)
            
            principles_signals['bonds_commodities_inverse'] = {
                'correlation': correlation,
                'signal': 'confirmed' if correlation < -0.5 else 'weak',
                'strength': abs(correlation) if correlation < 0 else 0
            }
        
        # Principle 2: Bonds lead Equities
        if 'bonds_equities' in murphy_data:
            bonds_yield = murphy_data['bonds_equities']['bonds']
            equities = murphy_data['bonds_equities']['equities']
            
            # Check if bond yield changes precede equity changes
            bonds_change = bonds_yield.pct_change()
            equities_change = equities.pct_change()
            
            # Calculate lead-lag correlation
            lead_correlation = bonds_change.shift(1).corr(equities_change)
            
            principles_signals['bonds_lead_equities'] = {
                'lead_correlation': lead_correlation,
                'signal': 'leading' if abs(lead_correlation) > 0.4 else 'weak',
                'strength': abs(lead_correlation)
            }
        
        return principles_signals
    
    def get_cross_market_confirmations(self, primary_asset: str):
        confirmations = {}
        intermarket_data = self.dataset_manager.synchronized_data
        
        if primary_asset not in intermarket_data:
            return confirmations
        
        primary_returns = intermarket_data[primary_asset]['close'].pct_change().tail(10)
        
        # Check confirmations across asset classes
        for asset_key, asset_data in intermarket_data.items():
            if asset_key != primary_asset and 'close' in asset_data.columns:
                asset_returns = asset_data['close'].pct_change().tail(10)
                correlation = primary_returns.corr(asset_returns)
                
                if abs(correlation) > 0.4:
                    confirmations[asset_key] = {
                        'correlation': correlation,
                        'confirmation': 'positive' if correlation > 0 else 'negative',
                        'strength': abs(correlation)
                    }
        
        return confirmations
    
    def analyze_leading_indicators(self):
        leading_signals = {}
        intermarket_data = self.dataset_manager.synchronized_data
        
        # EURJPY leads Nasdaq
        if 'forex_EURJPY' in intermarket_data and 'equities_NASDAQ' in intermarket_data:
            eurjpy = intermarket_data['forex_EURJPY']['close'].pct_change()
            nasdaq = intermarket_data['equities_NASDAQ']['close'].pct_change()
            
            # Check if EURJPY changes lead NASDAQ by 1-2 periods
            lead_corr = eurjpy.shift(1).corr(nasdaq)
            
            leading_signals['eurjpy_nasdaq'] = {
                'lead_correlation': lead_corr,
                'signal': 'leading' if abs(lead_corr) > 0.5 else 'weak',
                'current_eurjpy_signal': eurjpy.iloc[-1] if len(eurjpy) > 0 else 0
            }
        
        # Bond yield spreads lead currency pairs
        spreads = self.dataset_manager.get_bond_yield_spreads()
        
        if 'US_CA_10Y' in spreads and 'forex_USDCAD' in intermarket_data:
            spread_change = spreads['US_CA_10Y'].pct_change()
            usdcad_change = intermarket_data['forex_USDCAD']['close'].pct_change()
            
            lead_corr = spread_change.shift(1).corr(usdcad_change)
            
            leading_signals['bond_spread_usdcad'] = {
                'lead_correlation': lead_corr,
                'signal': 'leading' if abs(lead_corr) > 0.6 else 'weak',
                'current_spread_signal': spread_change.iloc[-1] if len(spread_change) > 0 else 0
            }
        
        return leading_signals
    
    def analyze_risk_sentiment(self):
        risk_signals = {}
        intermarket_data = self.dataset_manager.synchronized_data
        
        # VIX and equity correlation
        if 'equities_VIX' in intermarket_data and 'equities_SPX' in intermarket_data:
            vix = intermarket_data['equities_VIX']['close']
            spx = intermarket_data['equities_SPX']['close']
            
            vix_change = vix.pct_change().iloc[-1]
            spx_change = spx.pct_change().iloc[-1]
            
            if vix_change > 0.05:
                risk_signals['vix_spike'] = {
                    'signal': 'risk_off',
                    'strength': min(1.0, vix_change / 0.1),
                    'equity_confirmation': spx_change < -0.01
                }
        
        # Safe-haven flows (Gold, CHF, JPY)
        safe_haven_assets = ['commodities_XAUUSD', 'forex_USDCHF', 'forex_USDJPY']
        safe_haven_changes = []
        
        for asset in safe_haven_assets:
            if asset in intermarket_data:
                change = intermarket_data[asset]['close'].pct_change().iloc[-1]
                safe_haven_changes.append(change)
        
        if safe_haven_changes:
            avg_safe_haven = np.mean(safe_haven_changes)
            risk_signals['safe_haven_flow'] = {
                'signal': 'risk_off' if avg_safe_haven > 0.005 else 'risk_on' if avg_safe_haven < -0.005 else 'neutral',
                'strength': abs(avg_safe_haven) * 100,
                'assets_moving': len([x for x in safe_haven_changes if abs(x) > 0.005])
            }
        
        return risk_signals

class FATAIAFramework:
    
    def __init__(self, dataset_manager: IntermarketDatasetManager):
        self.fa_analyzer = FAAnalyzer()
        self.ta_analyzer = TAAnalyzer()
        self.ia_analyzer = IAAnalyzer(dataset_manager)
        self.dataset_manager = dataset_manager
    
    def comprehensive_analysis(self, currency_pair: str, indicators: List[EconomicIndicator]):
        analysis = {}
        
        # Get data for the currency pair
        forex_data = self.dataset_manager.get_asset_data(AssetType.FOREX, currency_pair)
        if not forex_data:
            return analysis
        
        # FA Analysis
        base_currency = CurrencyProfile(currency_pair[:3])
        quote_currency = CurrencyProfile(currency_pair[3:])
        
        base_fa = self.fa_analyzer.analyze_currency_fundamentals(base_currency, indicators)
        quote_fa = self.fa_analyzer.analyze_currency_fundamentals(quote_currency, indicators)
        
        analysis['fa'] = {
            'base_currency': base_fa,
            'quote_currency': quote_fa,
            'relative_strength': base_fa['fa_score'] - quote_fa['fa_score']
        }
        
        # TA Analysis  
        analysis['ta'] = self.ta_analyzer.analyze_technical_signals(forex_data.data)
        
        # IA Analysis
        analysis['ia'] = self.ia_analyzer.analyze_cross_market_signals(
            f"forex_{currency_pair}", 
            datetime.datetime.now(pytz.UTC)
        )
        
        # Integrated signals
        analysis['integrated_signals'] = self.generate_integrated_signals(analysis)
        
        return analysis
    
    def generate_integrated_signals(self, analysis: Dict):
        signals = {
            'trade_direction': 'neutral',
            'confidence': 0.0,
            'entry_timing': 'wait',
            'cross_market_confirmation': False,
            'risk_level': 'medium'
        }
        
        fa_score = analysis.get('fa', {}).get('relative_strength', 0)
        ta_signals = analysis.get('ta', {})
        ia_signals = analysis.get('ia', {})
        
        # FA direction
        fa_direction = 'bullish' if fa_score > 0.2 else 'bearish' if fa_score < -0.2 else 'neutral'
        
        # TA direction
        ta_entry_signals = ta_signals.get('entry_signals', [])
        ta_direction = 'neutral'
        if ta_entry_signals:
            long_signals = [s for s in ta_entry_signals if s['type'] == 'long']
            short_signals = [s for s in ta_entry_signals if s['type'] == 'short']
            
            if long_signals and not short_signals:
                ta_direction = 'bullish'
            elif short_signals and not long_signals:
                ta_direction = 'bearish'
        
        # IA confirmation
        murphy_signals = ia_signals.get('murphy_principles', {})
        confirmations = ia_signals.get('confirmations', {})
        
        ia_confirmation = False
        if murphy_signals or confirmations:
            confirmation_count = 0
            total_signals = 0
            
            for signal_data in murphy_signals.values():
                if signal_data.get('signal') == 'confirmed':
                    confirmation_count += 1
                total_signals += 1
            
            for conf_data in confirmations.values():
                if conf_data.get('strength', 0) > 0.5:
                    confirmation_count += 1
                total_signals += 1
            
            ia_confirmation = confirmation_count / max(1, total_signals) > 0.5
        
        # Integrate signals
        if fa_direction == ta_direction and fa_direction != 'neutral':
            signals['trade_direction'] = fa_direction
            signals['confidence'] = 0.7 if ia_confirmation else 0.5
            signals['entry_timing'] = 'good' if ta_entry_signals else 'wait'
            signals['cross_market_confirmation'] = ia_confirmation
        elif fa_direction != 'neutral' and ia_confirmation:
            signals['trade_direction'] = fa_direction
            signals['confidence'] = 0.6
            signals['entry_timing'] = 'wait'
            signals['cross_market_confirmation'] = True
        
        # Risk assessment
        risk_sentiment = ia_signals.get('risk_sentiment', {})
        if risk_sentiment.get('vix_spike', {}).get('signal') == 'risk_off':
            signals['risk_level'] = 'high'
        elif risk_sentiment.get('safe_haven_flow', {}).get('signal') == 'risk_off':
            signals['risk_level'] = 'high'
        else:
            signals['risk_level'] = 'medium'
        
        return signals