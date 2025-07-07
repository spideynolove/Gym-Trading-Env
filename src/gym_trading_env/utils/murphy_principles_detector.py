import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import datetime
import pytz
from .intermarket_dataset_manager import IntermarketDatasetManager, AssetType

class MurphyPrinciple(Enum):
    BONDS_VS_COMMODITIES = "bonds_vs_commodities"
    BONDS_LEAD_EQUITIES = "bonds_lead_equities"
    COMMODITIES_VS_CURRENCIES = "commodities_vs_currencies"
    CURRENCY_INTEREST_RATES = "currency_interest_rates"
    CROSS_MARKET_CONFIRMATION = "cross_market_confirmation"

@dataclass
class PrincipleSignal:
    principle: MurphyPrinciple
    signal_strength: float
    direction: str
    confidence: float
    supporting_data: Dict
    timestamp: datetime.datetime

class MurphyPrinciplesDetector:
    
    def __init__(self, dataset_manager: IntermarketDatasetManager):
        self.dataset_manager = dataset_manager
        self.principle_thresholds = {
            'strong_signal': 0.8,
            'moderate_signal': 0.6,
            'weak_signal': 0.4
        }
        self.correlation_windows = {
            'short_term': 20,
            'medium_term': 60,
            'long_term': 120
        }
    
    def detect_all_principles(self):
        principles_analysis = {}
        
        principles_analysis[MurphyPrinciple.BONDS_VS_COMMODITIES] = self.analyze_bonds_commodities_inverse()
        principles_analysis[MurphyPrinciple.BONDS_LEAD_EQUITIES] = self.analyze_bonds_lead_equities()
        principles_analysis[MurphyPrinciple.COMMODITIES_VS_CURRENCIES] = self.analyze_commodities_currencies_inverse()
        principles_analysis[MurphyPrinciple.CURRENCY_INTEREST_RATES] = self.analyze_currency_interest_rates()
        principles_analysis[MurphyPrinciple.CROSS_MARKET_CONFIRMATION] = self.analyze_cross_market_confirmation()
        
        return principles_analysis
    
    def analyze_bonds_commodities_inverse(self):
        bonds_data = self.dataset_manager.get_asset_data(AssetType.BONDS)
        commodities_data = self.dataset_manager.get_asset_data(AssetType.COMMODITIES)
        
        if not bonds_data or not commodities_data:
            return self.create_empty_signal(MurphyPrinciple.BONDS_VS_COMMODITIES)
        
        us10y = bonds_data.get('bonds_US10Y')
        crb_index = commodities_data.get('commodities_CRB_INDEX')
        
        if not us10y or not crb_index:
            return self.create_empty_signal(MurphyPrinciple.BONDS_VS_COMMODITIES)
        
        # Calculate correlations across different time windows
        bond_yields = us10y.data['close']
        commodity_prices = crb_index.data['close']
        
        correlations = {}
        for window_name, window_size in self.correlation_windows.items():
            if len(bond_yields) >= window_size and len(commodity_prices) >= window_size:
                bond_changes = bond_yields.pct_change().tail(window_size)
                commodity_changes = commodity_prices.pct_change().tail(window_size)
                correlations[window_name] = bond_changes.corr(commodity_changes)
        
        # Analyze inverse relationship strength
        avg_correlation = np.mean(list(correlations.values())) if correlations else 0
        inverse_strength = abs(avg_correlation) if avg_correlation < 0 else 0
        
        # Determine signal direction based on recent movements
        recent_bond_change = bond_yields.pct_change().tail(5).mean()
        recent_commodity_change = commodity_prices.pct_change().tail(5).mean()
        
        if recent_bond_change > 0.001 and recent_commodity_change < -0.001:
            direction = "bonds_rising_commodities_falling"
        elif recent_bond_change < -0.001 and recent_commodity_change > 0.001:
            direction = "bonds_falling_commodities_rising"
        else:
            direction = "neutral"
        
        confidence = min(1.0, inverse_strength * 2) if inverse_strength > 0.3 else 0.2
        
        return PrincipleSignal(
            principle=MurphyPrinciple.BONDS_VS_COMMODITIES,
            signal_strength=inverse_strength,
            direction=direction,
            confidence=confidence,
            supporting_data={
                'correlations': correlations,
                'recent_bond_change': recent_bond_change,
                'recent_commodity_change': recent_commodity_change,
                'principle_active': inverse_strength > 0.5
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def analyze_bonds_lead_equities(self):
        bonds_data = self.dataset_manager.get_asset_data(AssetType.BONDS)
        equities_data = self.dataset_manager.get_asset_data(AssetType.EQUITIES)
        
        if not bonds_data or not equities_data:
            return self.create_empty_signal(MurphyPrinciple.BONDS_LEAD_EQUITIES)
        
        us10y = bonds_data.get('bonds_US10Y')
        spx = equities_data.get('equities_SPX')
        
        if not us10y or not spx:
            return self.create_empty_signal(MurphyPrinciple.BONDS_LEAD_EQUITIES)
        
        bond_yields = us10y.data['close']
        equity_prices = spx.data['close']
        
        # Calculate lead-lag correlations
        bond_changes = bond_yields.pct_change()
        equity_changes = equity_prices.pct_change()
        
        lead_correlations = {}
        for lag in range(1, 6):  # Test 1-5 period leads
            if len(bond_changes) > lag and len(equity_changes) > lag:
                lead_corr = bond_changes.shift(lag).corr(equity_changes)
                lead_correlations[f'lag_{lag}'] = lead_corr
        
        # Find strongest leading relationship
        best_lag = max(lead_correlations.items(), key=lambda x: abs(x[1])) if lead_correlations else (None, 0)
        leading_strength = abs(best_lag[1]) if best_lag[1] else 0
        
        # Bond yield direction typically inverse to equity direction
        recent_bond_trend = bond_changes.tail(10).mean()
        recent_equity_trend = equity_changes.tail(10).mean()
        
        if recent_bond_trend > 0.001:
            expected_equity_direction = "falling"
            actual_equity_direction = "falling" if recent_equity_trend < 0 else "rising"
        elif recent_bond_trend < -0.001:
            expected_equity_direction = "rising"
            actual_equity_direction = "falling" if recent_equity_trend < 0 else "rising"
        else:
            expected_equity_direction = "neutral"
            actual_equity_direction = "neutral"
        
        direction_match = expected_equity_direction == actual_equity_direction
        confidence = leading_strength * (1.2 if direction_match else 0.8)
        
        return PrincipleSignal(
            principle=MurphyPrinciple.BONDS_LEAD_EQUITIES,
            signal_strength=leading_strength,
            direction=f"bonds_{'rising' if recent_bond_trend > 0 else 'falling'}_equities_{'rising' if recent_equity_trend > 0 else 'falling'}",
            confidence=min(1.0, confidence),
            supporting_data={
                'lead_correlations': lead_correlations,
                'best_lag': best_lag[0],
                'best_correlation': best_lag[1],
                'direction_match': direction_match,
                'principle_active': leading_strength > 0.4
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def analyze_commodities_currencies_inverse(self):
        commodities_data = self.dataset_manager.get_asset_data(AssetType.COMMODITIES)
        forex_data = self.dataset_manager.get_asset_data(AssetType.FOREX)
        
        if not commodities_data or not forex_data:
            return self.create_empty_signal(MurphyPrinciple.COMMODITIES_VS_CURRENCIES)
        
        # Focus on key relationships: Gold vs USD, Oil vs USD
        gold = commodities_data.get('commodities_XAUUSD')
        oil = commodities_data.get('commodities_WTIUSD')
        
        # Create USD index proxy from major pairs
        usd_pairs = {}
        for pair_name in ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD']:
            pair_data = forex_data.get(f'forex_{pair_name}')
            if pair_data:
                usd_pairs[pair_name] = 1 / pair_data.data['close']  # Invert to get USD strength
        
        if not (gold or oil) or not usd_pairs:
            return self.create_empty_signal(MurphyPrinciple.COMMODITIES_VS_CURRENCIES)
        
        # Calculate USD index as average of inverted major pairs
        usd_values = pd.DataFrame(usd_pairs)
        usd_index = usd_values.mean(axis=1)
        
        correlations = {}
        commodity_signals = {}
        
        # Gold vs USD correlation
        if gold:
            gold_changes = gold.data['close'].pct_change()
            usd_changes = usd_index.pct_change()
            
            # Align time series
            common_index = gold_changes.index.intersection(usd_changes.index)
            if len(common_index) > 20:
                gold_aligned = gold_changes.loc[common_index]
                usd_aligned = usd_changes.loc[common_index]
                
                gold_usd_corr = gold_aligned.tail(60).corr(usd_aligned.tail(60))
                correlations['gold_usd'] = gold_usd_corr
                
                # Recent signal strength
                recent_gold_trend = gold_aligned.tail(10).mean()
                recent_usd_trend = usd_aligned.tail(10).mean()
                
                commodity_signals['gold'] = {
                    'correlation': gold_usd_corr,
                    'inverse_strength': abs(gold_usd_corr) if gold_usd_corr < 0 else 0,
                    'recent_gold_trend': recent_gold_trend,
                    'recent_usd_trend': recent_usd_trend,
                    'principle_confirmed': gold_usd_corr < -0.5
                }
        
        # Oil vs USD correlation (for commodity currencies)
        if oil:
            oil_changes = oil.data['close'].pct_change()
            usd_changes = usd_index.pct_change()
            
            common_index = oil_changes.index.intersection(usd_changes.index)
            if len(common_index) > 20:
                oil_aligned = oil_changes.loc[common_index]
                usd_aligned = usd_changes.loc[common_index]
                
                oil_usd_corr = oil_aligned.tail(60).corr(usd_aligned.tail(60))
                correlations['oil_usd'] = oil_usd_corr
                
                commodity_signals['oil'] = {
                    'correlation': oil_usd_corr,
                    'inverse_strength': abs(oil_usd_corr) if oil_usd_corr < 0 else 0,
                    'principle_confirmed': oil_usd_corr < -0.3
                }
        
        # Overall signal strength
        inverse_strengths = [signal.get('inverse_strength', 0) for signal in commodity_signals.values()]
        avg_inverse_strength = np.mean(inverse_strengths) if inverse_strengths else 0
        
        # Direction assessment
        if commodity_signals.get('gold', {}).get('recent_gold_trend', 0) > 0.001:
            if commodity_signals.get('gold', {}).get('recent_usd_trend', 0) < -0.001:
                direction = "commodities_rising_usd_falling"
            else:
                direction = "mixed_signals"
        elif commodity_signals.get('gold', {}).get('recent_gold_trend', 0) < -0.001:
            if commodity_signals.get('gold', {}).get('recent_usd_trend', 0) > 0.001:
                direction = "commodities_falling_usd_rising"
            else:
                direction = "mixed_signals"
        else:
            direction = "neutral"
        
        confidence = min(1.0, avg_inverse_strength * 1.5) if avg_inverse_strength > 0.3 else 0.2
        
        return PrincipleSignal(
            principle=MurphyPrinciple.COMMODITIES_VS_CURRENCIES,
            signal_strength=avg_inverse_strength,
            direction=direction,
            confidence=confidence,
            supporting_data={
                'correlations': correlations,
                'commodity_signals': commodity_signals,
                'principle_active': avg_inverse_strength > 0.5
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def analyze_currency_interest_rates(self):
        bonds_data = self.dataset_manager.get_asset_data(AssetType.BONDS)
        forex_data = self.dataset_manager.get_asset_data(AssetType.FOREX)
        
        if not bonds_data or not forex_data:
            return self.create_empty_signal(MurphyPrinciple.CURRENCY_INTEREST_RATES)
        
        # Analyze interest rate differentials vs currency pairs
        currency_rate_analysis = {}
        
        # USDCAD vs US-Canada yield differential
        us10y = bonds_data.get('bonds_US10Y')
        ca10y = bonds_data.get('bonds_CA10Y')
        usdcad = forex_data.get('forex_USDCAD')
        
        if us10y and ca10y and usdcad:
            us_yield = us10y.data['close']
            ca_yield = ca10y.data['close']
            usdcad_rate = usdcad.data['close']
            
            # Calculate yield differential
            yield_differential = us_yield - ca_yield
            
            # Correlation between yield differential and USDCAD
            common_index = yield_differential.index.intersection(usdcad_rate.index)
            if len(common_index) > 60:
                diff_aligned = yield_differential.loc[common_index]
                usdcad_aligned = usdcad_rate.loc[common_index]
                
                correlation = diff_aligned.tail(60).corr(usdcad_aligned.tail(60))
                
                currency_rate_analysis['USDCAD'] = {
                    'correlation': correlation,
                    'current_differential': diff_aligned.iloc[-1] if len(diff_aligned) > 0 else 0,
                    'differential_trend': diff_aligned.tail(10).mean() - diff_aligned.tail(20).head(10).mean(),
                    'currency_response': correlation > 0.6
                }
        
        # GBPUSD vs UK-US yield differential
        uk10y = bonds_data.get('bonds_UK10Y')
        gbpusd = forex_data.get('forex_GBPUSD')
        
        if us10y and uk10y and gbpusd:
            us_yield = us10y.data['close']
            uk_yield = uk10y.data['close']
            gbpusd_rate = gbpusd.data['close']
            
            yield_differential = uk_yield - us_yield
            
            common_index = yield_differential.index.intersection(gbpusd_rate.index)
            if len(common_index) > 60:
                diff_aligned = yield_differential.loc[common_index]
                gbpusd_aligned = gbpusd_rate.loc[common_index]
                
                correlation = diff_aligned.tail(60).corr(gbpusd_aligned.tail(60))
                
                currency_rate_analysis['GBPUSD'] = {
                    'correlation': correlation,
                    'current_differential': diff_aligned.iloc[-1] if len(diff_aligned) > 0 else 0,
                    'differential_trend': diff_aligned.tail(10).mean() - diff_aligned.tail(20).head(10).mean(),
                    'currency_response': correlation > 0.6
                }
        
        # Overall principle strength
        correlations = [analysis.get('correlation', 0) for analysis in currency_rate_analysis.values()]
        avg_correlation = np.mean([abs(c) for c in correlations]) if correlations else 0
        
        # Direction based on strongest relationship
        strongest_pair = max(currency_rate_analysis.items(), 
                           key=lambda x: abs(x[1].get('correlation', 0))) if currency_rate_analysis else (None, {})
        
        if strongest_pair[1].get('differential_trend', 0) > 0.01:
            direction = f"{strongest_pair[0]}_positive_differential"
        elif strongest_pair[1].get('differential_trend', 0) < -0.01:
            direction = f"{strongest_pair[0]}_negative_differential"
        else:
            direction = "neutral"
        
        confidence = min(1.0, avg_correlation * 1.2) if avg_correlation > 0.4 else 0.3
        
        return PrincipleSignal(
            principle=MurphyPrinciple.CURRENCY_INTEREST_RATES,
            signal_strength=avg_correlation,
            direction=direction,
            confidence=confidence,
            supporting_data={
                'currency_rate_analysis': currency_rate_analysis,
                'principle_active': avg_correlation > 0.6
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def analyze_cross_market_confirmation(self):
        # This principle requires confirming signals across multiple markets
        all_principles = [
            self.analyze_bonds_commodities_inverse(),
            self.analyze_bonds_lead_equities(),
            self.analyze_commodities_currencies_inverse(),
            self.analyze_currency_interest_rates()
        ]
        
        # Count how many principles are actively signaling
        active_principles = sum(1 for p in all_principles if p.supporting_data.get('principle_active', False))
        total_principles = len(all_principles)
        
        # Calculate overall confirmation strength
        confirmation_ratio = active_principles / total_principles
        avg_confidence = np.mean([p.confidence for p in all_principles])
        
        # Direction based on consensus
        directions = [p.direction for p in all_principles if p.direction != 'neutral']
        direction_consensus = max(set(directions), key=directions.count) if directions else 'neutral'
        
        overall_strength = confirmation_ratio * avg_confidence
        
        return PrincipleSignal(
            principle=MurphyPrinciple.CROSS_MARKET_CONFIRMATION,
            signal_strength=overall_strength,
            direction=direction_consensus,
            confidence=min(1.0, overall_strength * 1.3),
            supporting_data={
                'active_principles': active_principles,
                'total_principles': total_principles,
                'confirmation_ratio': confirmation_ratio,
                'individual_principles': {p.principle.value: p.confidence for p in all_principles},
                'principle_active': confirmation_ratio > 0.6
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def create_empty_signal(self, principle: MurphyPrinciple):
        return PrincipleSignal(
            principle=principle,
            signal_strength=0.0,
            direction='neutral',
            confidence=0.0,
            supporting_data={'principle_active': False, 'error': 'insufficient_data'},
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def get_principle_summary(self):
        all_principles = self.detect_all_principles()
        
        summary = {
            'overall_signal_strength': 0.0,
            'active_principles_count': 0,
            'dominant_direction': 'neutral',
            'market_regime': 'normal',
            'principle_details': {}
        }
        
        # Calculate overall metrics
        active_count = 0
        total_strength = 0.0
        directions = []
        
        for principle, signal in all_principles.items():
            summary['principle_details'][principle.value] = {
                'strength': signal.signal_strength,
                'direction': signal.direction,
                'confidence': signal.confidence,
                'active': signal.supporting_data.get('principle_active', False)
            }
            
            if signal.supporting_data.get('principle_active', False):
                active_count += 1
                total_strength += signal.signal_strength
                if signal.direction != 'neutral':
                    directions.append(signal.direction)
        
        summary['active_principles_count'] = active_count
        summary['overall_signal_strength'] = total_strength / len(all_principles) if all_principles else 0
        
        if directions:
            summary['dominant_direction'] = max(set(directions), key=directions.count)
        
        # Determine market regime
        if summary['overall_signal_strength'] > 0.7 and active_count >= 3:
            summary['market_regime'] = 'strong_trending'
        elif summary['overall_signal_strength'] > 0.5 and active_count >= 2:
            summary['market_regime'] = 'trending'
        elif summary['overall_signal_strength'] < 0.3 or active_count == 0:
            summary['market_regime'] = 'consolidating'
        else:
            summary['market_regime'] = 'normal'
        
        return summary