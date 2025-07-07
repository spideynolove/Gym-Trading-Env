import datetime
import pytz
from typing import Dict, Any, Optional, List, Tuple
from .event_impact_manager import EventImpactManager
from .enhanced_cot_manager import EnhancedCOTManager
from .news_risk_manager import NewsRiskManager, EconomicEvent


class UnifiedMarketManager:
    
    def __init__(self, 
                 event_impact_manager: Optional[EventImpactManager] = None,
                 enhanced_cot_manager: Optional[EnhancedCOTManager] = None,
                 news_risk_manager: Optional[NewsRiskManager] = None):
        
        self.event_impact_manager = event_impact_manager or EventImpactManager()
        self.enhanced_cot_manager = enhanced_cot_manager or EnhancedCOTManager()
        self.news_risk_manager = news_risk_manager or NewsRiskManager()
    
    def get_comprehensive_market_analysis(self, currency_pair: str, 
                                        current_positions: Dict[str, float],
                                        timestamp: datetime.datetime = None) -> Dict[str, Any]:
        if timestamp is None:
            timestamp = datetime.datetime.now(pytz.UTC)
        
        # Extract currency from pair
        pair_clean = currency_pair.replace('/', '').replace('_', '')
        base_currency = pair_clean[:3]
        quote_currency = pair_clean[3:]
        
        analysis = {
            'currency_pair': currency_pair,
            'timestamp': timestamp,
            'base_currency': base_currency,
            'quote_currency': quote_currency
        }
        
        # 1. COT Analysis
        base_cot_signals = self.enhanced_cot_manager.get_cot_trading_signals(base_currency)
        quote_cot_signals = self.enhanced_cot_manager.get_cot_trading_signals(quote_currency)
        
        analysis['cot_analysis'] = {
            'base_currency_signals': base_cot_signals,
            'quote_currency_signals': quote_cot_signals,
            'net_cot_signal': self._calculate_net_cot_signal(base_cot_signals, quote_cot_signals)
        }
        
        # 2. Event Impact Analysis
        upcoming_events = self.news_risk_manager.get_upcoming_events(timestamp, hours_ahead=72)
        relevant_events = [e for e in upcoming_events 
                          if e.currency in [base_currency, quote_currency]]
        
        event_impacts = []
        for event in relevant_events:
            event_summary = self.event_impact_manager.get_event_impact_summary(event, current_positions)
            event_impacts.append(event_summary)
        
        analysis['event_impact_analysis'] = {
            'upcoming_events_count': len(relevant_events),
            'high_impact_events': [e for e in relevant_events if e.impact.value in ['High', 'Extreme']],
            'event_impacts': event_impacts,
            'portfolio_risk_concentration': self._calculate_event_risk_concentration(relevant_events, current_positions)
        }
        
        # 3. News Risk Assessment
        news_risk = self.news_risk_manager.get_risk_assessment(timestamp, currency_pair)
        analysis['news_risk_assessment'] = news_risk
        
        # 4. Integrated Position Recommendations
        analysis['integrated_recommendations'] = self._generate_integrated_recommendations(
            currency_pair, current_positions, analysis, timestamp
        )
        
        return analysis
    
    def _calculate_net_cot_signal(self, base_signals: Dict, quote_signals: Dict) -> Dict[str, Any]:
        base_confidence = base_signals.get('overall_confidence', 0)
        quote_confidence = quote_signals.get('overall_confidence', 0)
        
        # Determine net signal direction
        base_bullish_signals = sum(1 for s in base_signals.get('signals', []) 
                                 if 'BULLISH' in s.get('direction', ''))
        base_bearish_signals = sum(1 for s in base_signals.get('signals', []) 
                                 if 'BEARISH' in s.get('direction', ''))
        
        quote_bullish_signals = sum(1 for s in quote_signals.get('signals', []) 
                                  if 'BULLISH' in s.get('direction', ''))
        quote_bearish_signals = sum(1 for s in quote_signals.get('signals', []) 
                                  if 'BEARISH' in s.get('direction', ''))
        
        # Net signal for the currency pair (base vs quote)
        net_bullish = base_bullish_signals + quote_bearish_signals  # Base strong OR quote weak
        net_bearish = base_bearish_signals + quote_bullish_signals  # Base weak OR quote strong
        
        if net_bullish > net_bearish:
            direction = "BULLISH"
            strength = (net_bullish - net_bearish) / max(1, net_bullish + net_bearish)
        elif net_bearish > net_bullish:
            direction = "BEARISH"
            strength = (net_bearish - net_bullish) / max(1, net_bullish + net_bearish)
        else:
            direction = "NEUTRAL"
            strength = 0.0
        
        confidence = (base_confidence + quote_confidence) / 2
        
        return {
            'direction': direction,
            'strength': strength,
            'confidence': confidence,
            'base_signal_count': len(base_signals.get('signals', [])),
            'quote_signal_count': len(quote_signals.get('signals', []))
        }
    
    def _calculate_event_risk_concentration(self, events: List[EconomicEvent], 
                                          positions: Dict[str, float]) -> Dict[str, Any]:
        if not events or not positions:
            return {'risk_level': 'LOW', 'total_exposure': 0.0}
        
        total_exposure = 0.0
        for event in events:
            risk_analysis = self.event_impact_manager.get_risk_concentration_analysis(event, positions)
            total_exposure += risk_analysis.get('total_exposure', 0.0)
        
        if total_exposure > 3.0:
            risk_level = "EXTREME"
        elif total_exposure > 2.0:
            risk_level = "HIGH"
        elif total_exposure > 1.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            'risk_level': risk_level,
            'total_exposure': total_exposure,
            'event_count': len(events),
            'avg_exposure_per_event': total_exposure / len(events)
        }
    
    def _generate_integrated_recommendations(self, currency_pair: str, 
                                           current_positions: Dict[str, float],
                                           analysis: Dict[str, Any],
                                           timestamp: datetime.datetime) -> Dict[str, Any]:
        
        recommendations = {
            'position_adjustments': {},
            'risk_warnings': [],
            'trading_opportunities': [],
            'overall_sentiment': 'NEUTRAL',
            'confidence_level': 0.0
        }
        
        # COT-based recommendations
        cot_signal = analysis['cot_analysis']['net_cot_signal']
        if cot_signal['confidence'] > 0.6:
            if cot_signal['direction'] == 'BULLISH':
                recommendations['trading_opportunities'].append({
                    'type': 'COT_CONTRARIAN',
                    'direction': 'LONG',
                    'confidence': cot_signal['confidence'],
                    'reason': f"COT analysis shows bullish sentiment (strength: {cot_signal['strength']:.2f})"
                })
            elif cot_signal['direction'] == 'BEARISH':
                recommendations['trading_opportunities'].append({
                    'type': 'COT_CONTRARIAN',
                    'direction': 'SHORT',
                    'confidence': cot_signal['confidence'],
                    'reason': f"COT analysis shows bearish sentiment (strength: {cot_signal['strength']:.2f})"
                })
        
        # Event-based recommendations
        event_risk = analysis['event_impact_analysis']['portfolio_risk_concentration']
        if event_risk['risk_level'] in ['HIGH', 'EXTREME']:
            recommendations['risk_warnings'].append({
                'type': 'EVENT_CONCENTRATION',
                'severity': event_risk['risk_level'],
                'message': f"High event risk exposure: {event_risk['total_exposure']:.1f}"
            })
            
            # Suggest position reductions
            current_position = current_positions.get(currency_pair, 0.0)
            if abs(current_position) > 0.1:
                reduction_factor = 0.3 if event_risk['risk_level'] == 'HIGH' else 0.5
                recommended_position = current_position * (1 - reduction_factor)
                recommendations['position_adjustments'][currency_pair] = recommended_position
        
        # News risk recommendations
        news_risk = analysis['news_risk_assessment']
        if news_risk['should_avoid_trading']:
            recommendations['risk_warnings'].append({
                'type': 'NEWS_RESTRICTION',
                'severity': 'HIGH',
                'message': f"Avoid trading due to {news_risk['affected_event']}"
            })
        
        if news_risk['position_size_multiplier'] < 1.0:
            current_position = current_positions.get(currency_pair, 0.0)
            adjusted_position = current_position * news_risk['position_size_multiplier']
            recommendations['position_adjustments'][currency_pair] = adjusted_position
        
        # Overall sentiment calculation
        signals = []
        confidences = []
        
        if cot_signal['confidence'] > 0.5:
            signals.append(cot_signal['direction'])
            confidences.append(cot_signal['confidence'])
        
        if news_risk['volatility_forecast'] > 2.0:
            signals.append('HIGH_VOLATILITY')
            confidences.append(0.7)
        
        if signals:
            # Determine overall sentiment
            bullish_count = signals.count('BULLISH')
            bearish_count = signals.count('BEARISH')
            
            if bullish_count > bearish_count:
                recommendations['overall_sentiment'] = 'BULLISH'
            elif bearish_count > bullish_count:
                recommendations['overall_sentiment'] = 'BEARISH'
            else:
                recommendations['overall_sentiment'] = 'NEUTRAL'
            
            recommendations['confidence_level'] = sum(confidences) / len(confidences)
        
        return recommendations
    
    def get_dynamic_unified_features(self, currency_pair: str, 
                                   current_positions: Dict[str, float],
                                   timestamp: datetime.datetime = None) -> Dict[str, float]:
        if timestamp is None:
            timestamp = datetime.datetime.now(pytz.UTC)
        
        analysis = self.get_comprehensive_market_analysis(currency_pair, current_positions, timestamp)
        
        # Extract currency
        pair_clean = currency_pair.replace('/', '').replace('_', '')
        base_currency = pair_clean[:3]
        
        # COT features
        base_cot = analysis['cot_analysis']['base_currency_signals']
        cot_net_signal = analysis['cot_analysis']['net_cot_signal']
        
        # Event features
        event_risk = analysis['event_impact_analysis']['portfolio_risk_concentration']
        high_impact_events = len(analysis['event_impact_analysis']['high_impact_events'])
        
        # News features
        news_risk = analysis['news_risk_assessment']
        
        # Recommendation features
        recommendations = analysis['integrated_recommendations']
        
        return {
            'cot_signal_strength': cot_net_signal.get('strength', 0.0),
            'cot_signal_confidence': cot_net_signal.get('confidence', 0.0),
            'cot_bullish_signal': 1.0 if cot_net_signal.get('direction') == 'BULLISH' else 0.0,
            'cot_bearish_signal': 1.0 if cot_net_signal.get('direction') == 'BEARISH' else 0.0,
            'event_risk_level': {'LOW': 0.25, 'MEDIUM': 0.5, 'HIGH': 0.75, 'EXTREME': 1.0}.get(event_risk['risk_level'], 0.25),
            'event_exposure': min(1.0, event_risk['total_exposure'] / 3.0),  # Normalize to 0-1
            'high_impact_events_count': min(1.0, high_impact_events / 5.0),  # Normalize to 0-1
            'news_position_multiplier': news_risk['position_size_multiplier'],
            'news_volatility_forecast': min(1.0, news_risk['volatility_forecast'] / 5.0),  # Normalize to 0-1
            'overall_sentiment_bullish': 1.0 if recommendations['overall_sentiment'] == 'BULLISH' else 0.0,
            'overall_sentiment_bearish': 1.0 if recommendations['overall_sentiment'] == 'BEARISH' else 0.0,
            'integrated_confidence': recommendations['confidence_level'],
            'risk_warning_count': min(1.0, len(recommendations['risk_warnings']) / 3.0),  # Normalize to 0-1
            'trading_opportunity_count': min(1.0, len(recommendations['trading_opportunities']) / 3.0)  # Normalize to 0-1
        }
    
    def should_restrict_trading_integrated(self, currency_pair: str, 
                                         current_positions: Dict[str, float],
                                         timestamp: datetime.datetime = None) -> Tuple[bool, str]:
        analysis = self.get_comprehensive_market_analysis(currency_pair, current_positions, timestamp)
        
        # Check various restriction conditions
        restrictions = []
        
        # News-based restrictions
        news_risk = analysis['news_risk_assessment']
        if news_risk['should_avoid_trading']:
            restrictions.append(f"News event restriction: {news_risk['affected_event']}")
        
        # Event concentration restrictions
        event_risk = analysis['event_impact_analysis']['portfolio_risk_concentration']
        if event_risk['risk_level'] == 'EXTREME':
            restrictions.append(f"Extreme event risk concentration: {event_risk['total_exposure']:.1f}")
        
        # High volatility restrictions
        if news_risk['volatility_forecast'] > 4.0:
            restrictions.append(f"Extreme volatility forecast: {news_risk['volatility_forecast']:.1f}x")
        
        should_restrict = len(restrictions) > 0
        reason = "; ".join(restrictions) if restrictions else "No restrictions"
        
        return should_restrict, reason
    
    def get_optimal_position_size_integrated(self, currency_pair: str, 
                                           base_position_size: float,
                                           current_positions: Dict[str, float],
                                           timestamp: datetime.datetime = None) -> float:
        analysis = self.get_comprehensive_market_analysis(currency_pair, current_positions, timestamp)
        
        adjustments = []
        
        # News-based adjustment
        news_multiplier = analysis['news_risk_assessment']['position_size_multiplier']
        adjustments.append(news_multiplier)
        
        # Event risk adjustment
        event_risk = analysis['event_impact_analysis']['portfolio_risk_concentration']
        if event_risk['risk_level'] == 'EXTREME':
            event_multiplier = 0.2
        elif event_risk['risk_level'] == 'HIGH':
            event_multiplier = 0.5
        elif event_risk['risk_level'] == 'MEDIUM':
            event_multiplier = 0.8
        else:
            event_multiplier = 1.0
        adjustments.append(event_multiplier)
        
        # COT-based adjustment (increase size for high-confidence signals)
        cot_signal = analysis['cot_analysis']['net_cot_signal']
        if cot_signal['confidence'] > 0.8:
            cot_multiplier = 1.2  # Increase position for high-confidence COT signals
        elif cot_signal['confidence'] > 0.6:
            cot_multiplier = 1.1
        else:
            cot_multiplier = 1.0
        adjustments.append(cot_multiplier)
        
        # Apply all adjustments
        final_multiplier = 1.0
        for adjustment in adjustments:
            final_multiplier *= adjustment
        
        return base_position_size * final_multiplier


def dynamic_feature_unified_cot_signal_strength(history):
    manager = UnifiedMarketManager()
    
    # Should be parameterized in real implementation
    currency_pair = "EUR/USD"
    current_positions = {}
    
    current_timestamp = history.df.index[history._idx] if hasattr(history, 'df') else datetime.datetime.now(pytz.UTC)
    features = manager.get_dynamic_unified_features(currency_pair, current_positions, current_timestamp)
    return features['cot_signal_strength']


def dynamic_feature_unified_event_risk_level(history):
    manager = UnifiedMarketManager()
    
    currency_pair = "EUR/USD"
    current_positions = {}
    
    current_timestamp = history.df.index[history._idx] if hasattr(history, 'df') else datetime.datetime.now(pytz.UTC)
    features = manager.get_dynamic_unified_features(currency_pair, current_positions, current_timestamp)
    return features['event_risk_level']


def dynamic_feature_unified_integrated_confidence(history):
    manager = UnifiedMarketManager()
    
    currency_pair = "EUR/USD"
    current_positions = {}
    
    current_timestamp = history.df.index[history._idx] if hasattr(history, 'df') else datetime.datetime.now(pytz.UTC)
    features = manager.get_dynamic_unified_features(currency_pair, current_positions, current_timestamp)
    return features['integrated_confidence']