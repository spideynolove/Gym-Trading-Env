import datetime
import pytz
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import math


class TraderCategory(Enum):
    COMMERCIAL = "Commercial"
    NON_COMMERCIAL = "Non-Commercial"
    RETAIL = "Retail"
    ASSET_MANAGER = "Asset Manager"
    LEVERAGED_FUND = "Leveraged Fund"
    OTHER_REPORTABLE = "Other Reportable"


class PositionType(Enum):
    LONG = "Long"
    SHORT = "Short"
    NET = "Net"


class SentimentSignal(Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"
    EXTREME_BULLISH = "Extreme Bullish"
    EXTREME_BEARISH = "Extreme Bearish"


@dataclass
class COTPosition:
    currency: str
    trader_category: TraderCategory
    position_type: PositionType
    contracts: int
    percentage_of_open_interest: float
    change_from_previous: int
    timestamp: datetime.datetime
    
    def get_position_size_normalized(self) -> float:
        return self.contracts / 100000  # Normalize to standard lots


@dataclass
class COTSentimentReading:
    currency: str
    timestamp: datetime.datetime
    commercial_sentiment: SentimentSignal
    speculative_sentiment: SentimentSignal
    retail_sentiment: SentimentSignal
    contrarian_signal: SentimentSignal
    confidence_level: float
    extremity_score: float  # 0-1, where 1 is most extreme
    
    def is_contrarian_opportunity(self) -> bool:
        return (self.extremity_score > 0.8 and 
                self.contrarian_signal in [SentimentSignal.EXTREME_BULLISH, SentimentSignal.EXTREME_BEARISH])


class EnhancedCOTManager:
    
    def __init__(self):
        self.cot_data: Dict[str, List[COTPosition]] = {}
        self.sentiment_history: Dict[str, List[COTSentimentReading]] = {}
        
        # Currency mappings for COT futures contracts
        self.currency_contracts = {
            'EUR': 'Euro FX',
            'GBP': 'British Pound',
            'JPY': 'Japanese Yen',
            'CHF': 'Swiss Franc',
            'CAD': 'Canadian Dollar',
            'AUD': 'Australian Dollar',
            'NZD': 'New Zealand Dollar',
            'USD': 'US Dollar Index'
        }
        
        # Extremity thresholds (percentiles)
        self.extremity_thresholds = {
            'extreme_high': 90,  # 90th percentile
            'high': 75,         # 75th percentile
            'low': 25,          # 25th percentile
            'extreme_low': 10   # 10th percentile
        }
        
        # Historical ranges for percentile calculations (simulated)
        self.historical_ranges = {
            'EUR': {'commercial_net': (-150000, 250000), 'speculative_net': (-200000, 200000)},
            'GBP': {'commercial_net': (-100000, 150000), 'speculative_net': (-120000, 120000)},
            'JPY': {'commercial_net': (-80000, 120000), 'speculative_net': (-100000, 100000)},
            'CHF': {'commercial_net': (-50000, 80000), 'speculative_net': (-60000, 60000)},
            'CAD': {'commercial_net': (-80000, 100000), 'speculative_net': (-90000, 90000)},
            'AUD': {'commercial_net': (-60000, 90000), 'speculative_net': (-80000, 80000)},
            'NZD': {'commercial_net': (-30000, 50000), 'speculative_net': (-40000, 40000)}
        }
        
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        base_date = datetime.datetime(2024, 1, 1, tzinfo=pytz.UTC)
        
        # Generate 12 weeks of sample COT data
        for week in range(12):
            report_date = base_date + datetime.timedelta(weeks=week)
            
            for currency in ['EUR', 'GBP', 'JPY', 'CHF']:
                self._generate_sample_week_data(currency, report_date)
    
    def _generate_sample_week_data(self, currency: str, report_date: datetime.datetime):
        if currency not in self.cot_data:
            self.cot_data[currency] = []
        
        # Generate realistic COT positions with some patterns
        import random
        random.seed(hash(currency + str(report_date.day)))
        
        base_contracts = {
            'EUR': 150000, 'GBP': 80000, 'JPY': 60000, 'CHF': 40000
        }[currency]
        
        # Commercial hedgers (typically net short in currency futures)
        commercial_long = int(base_contracts * (0.3 + random.gauss(0, 0.1)))
        commercial_short = int(base_contracts * (0.7 + random.gauss(0, 0.15)))
        
        # Large speculators (trend followers)
        speculative_long = int(base_contracts * (0.4 + random.gauss(0, 0.2)))
        speculative_short = int(base_contracts * (0.3 + random.gauss(0, 0.15)))
        
        # Small speculators (retail-like)
        retail_long = int(base_contracts * (0.2 + random.gauss(0, 0.05)))
        retail_short = int(base_contracts * (0.15 + random.gauss(0, 0.05)))
        
        # Asset managers (disaggregated data)
        asset_mgr_long = int(speculative_long * 0.6)
        asset_mgr_short = int(speculative_short * 0.4)
        
        # Leveraged funds (disaggregated data)
        leveraged_long = int(speculative_long * 0.4)
        leveraged_short = int(speculative_short * 0.6)
        
        total_open_interest = commercial_long + commercial_short + speculative_long + speculative_short + retail_long + retail_short
        
        positions = [
            # Commercial positions
            COTPosition(currency, TraderCategory.COMMERCIAL, PositionType.LONG, 
                       commercial_long, commercial_long/total_open_interest*100, 
                       random.randint(-5000, 5000), report_date),
            COTPosition(currency, TraderCategory.COMMERCIAL, PositionType.SHORT, 
                       commercial_short, commercial_short/total_open_interest*100, 
                       random.randint(-5000, 5000), report_date),
            
            # Non-commercial positions
            COTPosition(currency, TraderCategory.NON_COMMERCIAL, PositionType.LONG, 
                       speculative_long, speculative_long/total_open_interest*100, 
                       random.randint(-3000, 3000), report_date),
            COTPosition(currency, TraderCategory.NON_COMMERCIAL, PositionType.SHORT, 
                       speculative_short, speculative_short/total_open_interest*100, 
                       random.randint(-3000, 3000), report_date),
            
            # Retail positions
            COTPosition(currency, TraderCategory.RETAIL, PositionType.LONG, 
                       retail_long, retail_long/total_open_interest*100, 
                       random.randint(-1000, 1000), report_date),
            COTPosition(currency, TraderCategory.RETAIL, PositionType.SHORT, 
                       retail_short, retail_short/total_open_interest*100, 
                       random.randint(-1000, 1000), report_date),
            
            # Disaggregated data
            COTPosition(currency, TraderCategory.ASSET_MANAGER, PositionType.LONG, 
                       asset_mgr_long, asset_mgr_long/total_open_interest*100, 
                       random.randint(-2000, 2000), report_date),
            COTPosition(currency, TraderCategory.ASSET_MANAGER, PositionType.SHORT, 
                       asset_mgr_short, asset_mgr_short/total_open_interest*100, 
                       random.randint(-2000, 2000), report_date),
            
            COTPosition(currency, TraderCategory.LEVERAGED_FUND, PositionType.LONG, 
                       leveraged_long, leveraged_long/total_open_interest*100, 
                       random.randint(-2000, 2000), report_date),
            COTPosition(currency, TraderCategory.LEVERAGED_FUND, PositionType.SHORT, 
                       leveraged_short, leveraged_short/total_open_interest*100, 
                       random.randint(-2000, 2000), report_date)
        ]
        
        self.cot_data[currency].extend(positions)
    
    def add_cot_position(self, position: COTPosition):
        if position.currency not in self.cot_data:
            self.cot_data[position.currency] = []
        
        self.cot_data[position.currency].append(position)
        
        # Keep only last 52 weeks of data (1 year)
        if len(self.cot_data[position.currency]) > 520:  # 52 weeks * 10 categories
            self.cot_data[position.currency] = self.cot_data[position.currency][-520:]
    
    def get_net_position(self, currency: str, trader_category: TraderCategory, 
                        timestamp: datetime.datetime = None) -> Optional[int]:
        if currency not in self.cot_data:
            return None
        
        if timestamp is None:
            timestamp = datetime.datetime.now(pytz.UTC)
        
        # Find the most recent data for the given timestamp
        relevant_positions = [
            pos for pos in self.cot_data[currency] 
            if pos.trader_category == trader_category and pos.timestamp <= timestamp
        ]
        
        if not relevant_positions:
            return None
        
        # Get the most recent week's data
        latest_date = max(pos.timestamp for pos in relevant_positions)
        latest_positions = [
            pos for pos in relevant_positions 
            if pos.timestamp == latest_date
        ]
        
        long_contracts = sum(pos.contracts for pos in latest_positions if pos.position_type == PositionType.LONG)
        short_contracts = sum(pos.contracts for pos in latest_positions if pos.position_type == PositionType.SHORT)
        
        return long_contracts - short_contracts
    
    def calculate_position_percentile(self, currency: str, trader_category: TraderCategory, 
                                    current_net_position: int) -> float:
        if currency not in self.historical_ranges:
            return 50.0  # Default to 50th percentile
        
        if trader_category == TraderCategory.COMMERCIAL:
            range_key = 'commercial_net'
        else:
            range_key = 'speculative_net'
        
        min_val, max_val = self.historical_ranges[currency][range_key]
        
        if max_val == min_val:
            return 50.0
        
        percentile = ((current_net_position - min_val) / (max_val - min_val)) * 100
        return max(0, min(100, percentile))
    
    def classify_sentiment(self, percentile: float) -> SentimentSignal:
        if percentile >= self.extremity_thresholds['extreme_high']:
            return SentimentSignal.EXTREME_BULLISH
        elif percentile >= self.extremity_thresholds['high']:
            return SentimentSignal.BULLISH
        elif percentile <= self.extremity_thresholds['extreme_low']:
            return SentimentSignal.EXTREME_BEARISH
        elif percentile <= self.extremity_thresholds['low']:
            return SentimentSignal.BEARISH
        else:
            return SentimentSignal.NEUTRAL
    
    def calculate_extremity_score(self, percentile: float) -> float:
        # Calculate how extreme the position is (0-1 scale)
        if percentile >= 50:
            # Bullish extreme
            return (percentile - 50) / 50
        else:
            # Bearish extreme
            return (50 - percentile) / 50
    
    def generate_contrarian_signal(self, commercial_sentiment: SentimentSignal, 
                                 speculative_sentiment: SentimentSignal,
                                 retail_sentiment: SentimentSignal) -> SentimentSignal:
        # Commercial hedgers are typically contrarian indicators
        # When commercials are extremely positioned, market often reverses
        
        if commercial_sentiment == SentimentSignal.EXTREME_BEARISH:
            # Commercials extremely short -> bullish contrarian signal
            return SentimentSignal.EXTREME_BULLISH
        elif commercial_sentiment == SentimentSignal.EXTREME_BULLISH:
            # Commercials extremely long -> bearish contrarian signal
            return SentimentSignal.EXTREME_BEARISH
        elif commercial_sentiment == SentimentSignal.BEARISH:
            return SentimentSignal.BULLISH
        elif commercial_sentiment == SentimentSignal.BULLISH:
            return SentimentSignal.BEARISH
        else:
            # Also consider retail positioning for contrarian signals
            if retail_sentiment == SentimentSignal.EXTREME_BULLISH:
                return SentimentSignal.BEARISH
            elif retail_sentiment == SentimentSignal.EXTREME_BEARISH:
                return SentimentSignal.BULLISH
            else:
                return SentimentSignal.NEUTRAL
    
    def analyze_cot_sentiment(self, currency: str, timestamp: datetime.datetime = None) -> Optional[COTSentimentReading]:
        if timestamp is None:
            timestamp = datetime.datetime.now(pytz.UTC)
        
        # Get net positions for each trader category
        commercial_net = self.get_net_position(currency, TraderCategory.COMMERCIAL, timestamp)
        speculative_net = self.get_net_position(currency, TraderCategory.NON_COMMERCIAL, timestamp)
        retail_net = self.get_net_position(currency, TraderCategory.RETAIL, timestamp)
        
        if commercial_net is None or speculative_net is None or retail_net is None:
            return None
        
        # Calculate percentiles
        commercial_percentile = self.calculate_position_percentile(currency, TraderCategory.COMMERCIAL, commercial_net)
        speculative_percentile = self.calculate_position_percentile(currency, TraderCategory.NON_COMMERCIAL, speculative_net)
        retail_percentile = self.calculate_position_percentile(currency, TraderCategory.RETAIL, retail_net)
        
        # Classify sentiments
        commercial_sentiment = self.classify_sentiment(commercial_percentile)
        speculative_sentiment = self.classify_sentiment(speculative_percentile)
        retail_sentiment = self.classify_sentiment(retail_percentile)
        
        # Generate contrarian signal
        contrarian_signal = self.generate_contrarian_signal(commercial_sentiment, speculative_sentiment, retail_sentiment)
        
        # Calculate overall extremity score
        extremity_scores = [
            self.calculate_extremity_score(commercial_percentile),
            self.calculate_extremity_score(speculative_percentile),
            self.calculate_extremity_score(retail_percentile)
        ]
        overall_extremity = max(extremity_scores)
        
        # Calculate confidence level
        confidence = self._calculate_sentiment_confidence(commercial_percentile, speculative_percentile, retail_percentile)
        
        return COTSentimentReading(
            currency=currency,
            timestamp=timestamp,
            commercial_sentiment=commercial_sentiment,
            speculative_sentiment=speculative_sentiment,
            retail_sentiment=retail_sentiment,
            contrarian_signal=contrarian_signal,
            confidence_level=confidence,
            extremity_score=overall_extremity
        )
    
    def _calculate_sentiment_confidence(self, comm_percentile: float, spec_percentile: float, retail_percentile: float) -> float:
        # Higher confidence when:
        # 1. Positions are more extreme
        # 2. Commercial and speculative positions diverge (typical pattern)
        # 3. Clear directional bias
        
        extremity_factor = max(
            abs(comm_percentile - 50),
            abs(spec_percentile - 50),
            abs(retail_percentile - 50)
        ) / 50.0
        
        # Divergence between commercial and speculative (good sign)
        divergence_factor = abs(comm_percentile - spec_percentile) / 100.0
        
        # Clear directional bias
        direction_clarity = abs((comm_percentile + spec_percentile + retail_percentile) / 3 - 50) / 50.0
        
        base_confidence = 0.5
        confidence = base_confidence + (extremity_factor * 0.3) + (divergence_factor * 0.15) + (direction_clarity * 0.05)
        
        return min(1.0, max(0.1, confidence))
    
    def get_smart_money_vs_dumb_money_analysis(self, currency: str, timestamp: datetime.datetime = None) -> Dict[str, any]:
        if timestamp is None:
            timestamp = datetime.datetime.now(pytz.UTC)
        
        # Smart money: Commercial hedgers, Asset managers
        # Dumb money: Leveraged funds, Retail
        
        commercial_net = self.get_net_position(currency, TraderCategory.COMMERCIAL, timestamp)
        asset_mgr_net = self.get_net_position(currency, TraderCategory.ASSET_MANAGER, timestamp)
        leveraged_net = self.get_net_position(currency, TraderCategory.LEVERAGED_FUND, timestamp)
        retail_net = self.get_net_position(currency, TraderCategory.RETAIL, timestamp)
        
        smart_money_net = (commercial_net or 0) + (asset_mgr_net or 0)
        dumb_money_net = (leveraged_net or 0) + (retail_net or 0)
        
        # Calculate the ratio
        if dumb_money_net != 0:
            smart_dumb_ratio = smart_money_net / abs(dumb_money_net)
        else:
            smart_dumb_ratio = 0
        
        # Determine signal strength
        if smart_dumb_ratio > 2:
            signal = "STRONG_BULLISH"
        elif smart_dumb_ratio > 1:
            signal = "BULLISH"
        elif smart_dumb_ratio < -2:
            signal = "STRONG_BEARISH"
        elif smart_dumb_ratio < -1:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        
        return {
            'currency': currency,
            'smart_money_net': smart_money_net,
            'dumb_money_net': dumb_money_net,
            'smart_dumb_ratio': smart_dumb_ratio,
            'signal': signal,
            'commercial_net': commercial_net,
            'asset_manager_net': asset_mgr_net,
            'leveraged_fund_net': leveraged_net,
            'retail_net': retail_net
        }
    
    def get_cot_momentum_analysis(self, currency: str, weeks_lookback: int = 4) -> Dict[str, any]:
        current_time = datetime.datetime.now(pytz.UTC)
        
        momentum_data = []
        for week in range(weeks_lookback):
            week_date = current_time - datetime.timedelta(weeks=week)
            sentiment = self.analyze_cot_sentiment(currency, week_date)
            if sentiment:
                momentum_data.append({
                    'week': week,
                    'commercial_sentiment': sentiment.commercial_sentiment.value,
                    'speculative_sentiment': sentiment.speculative_sentiment.value,
                    'contrarian_signal': sentiment.contrarian_signal.value,
                    'extremity_score': sentiment.extremity_score
                })
        
        if not momentum_data:
            return {'currency': currency, 'momentum_trend': 'UNKNOWN', 'data': []}
        
        # Analyze momentum trends
        extremity_trend = [data['extremity_score'] for data in momentum_data]
        
        if len(extremity_trend) >= 2:
            recent_change = extremity_trend[0] - extremity_trend[1]
            if recent_change > 0.1:
                momentum_trend = "INCREASING_EXTREMITY"
            elif recent_change < -0.1:
                momentum_trend = "DECREASING_EXTREMITY"
            else:
                momentum_trend = "STABLE"
        else:
            momentum_trend = "INSUFFICIENT_DATA"
        
        return {
            'currency': currency,
            'momentum_trend': momentum_trend,
            'weeks_analyzed': len(momentum_data),
            'current_extremity': extremity_trend[0] if extremity_trend else 0,
            'data': momentum_data
        }
    
    def get_cot_trading_signals(self, currency: str) -> Dict[str, any]:
        sentiment = self.analyze_cot_sentiment(currency)
        smart_dumb = self.get_smart_money_vs_dumb_money_analysis(currency)
        momentum = self.get_cot_momentum_analysis(currency)
        
        if not sentiment:
            return {'currency': currency, 'signals': [], 'confidence': 0.0}
        
        signals = []
        total_confidence = 0.0
        signal_count = 0
        
        # Contrarian signal from sentiment analysis
        if sentiment.is_contrarian_opportunity():
            signals.append({
                'type': 'CONTRARIAN',
                'direction': sentiment.contrarian_signal.value,
                'confidence': sentiment.confidence_level,
                'reason': f"Extreme positioning detected (extremity: {sentiment.extremity_score:.2f})"
            })
            total_confidence += sentiment.confidence_level
            signal_count += 1
        
        # Smart money vs dumb money signal
        if smart_dumb['signal'] != 'NEUTRAL':
            signals.append({
                'type': 'SMART_MONEY',
                'direction': smart_dumb['signal'],
                'confidence': 0.7,
                'reason': f"Smart/Dumb money ratio: {smart_dumb['smart_dumb_ratio']:.2f}"
            })
            total_confidence += 0.7
            signal_count += 1
        
        # Momentum-based signal
        if momentum['momentum_trend'] == 'INCREASING_EXTREMITY':
            signals.append({
                'type': 'MOMENTUM',
                'direction': 'STRENGTHENING',
                'confidence': 0.6,
                'reason': f"Positioning extremity increasing: {momentum['current_extremity']:.2f}"
            })
            total_confidence += 0.6
            signal_count += 1
        
        average_confidence = total_confidence / signal_count if signal_count > 0 else 0.0
        
        return {
            'currency': currency,
            'signals': signals,
            'overall_confidence': average_confidence,
            'sentiment_data': sentiment,
            'smart_dumb_analysis': smart_dumb,
            'momentum_analysis': momentum
        }