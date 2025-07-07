import datetime
import pytz
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import math
from .news_risk_manager import EconomicEvent, EventImpact, EventCategory


class SpilloverType(Enum):
    DIRECT = "Direct"
    INDIRECT = "Indirect"
    CROSS_CURRENCY = "Cross-Currency"
    RISK_ON_OFF = "Risk-On-Off"


@dataclass
class EventSpillover:
    source_event: EconomicEvent
    affected_pair: str
    spillover_type: SpilloverType
    impact_coefficient: float
    transmission_delay: int  # minutes
    confidence_level: float
    
    def get_adjusted_impact(self) -> float:
        return self.impact_coefficient * self.confidence_level


class EventImpactManager:
    
    def __init__(self):
        self.currency_hierarchy = {
            'USD': 1.0,    # Primary reserve currency
            'EUR': 0.85,   # Major reserve currency
            'GBP': 0.75,   # Major trading currency
            'JPY': 0.70,   # Safe haven currency
            'CHF': 0.60,   # Safe haven currency
            'CAD': 0.50,   # Commodity currency
            'AUD': 0.45,   # Commodity currency
            'NZD': 0.35    # Commodity currency
        }
        
        self.major_pairs = [
            'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF',
            'AUD/USD', 'USD/CAD', 'NZD/USD'
        ]
        
        self.cross_pairs = [
            'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/AUD', 'EUR/CAD',
            'GBP/JPY', 'GBP/CHF', 'GBP/AUD', 'GBP/CAD',
            'AUD/JPY', 'AUD/CAD', 'CAD/JPY', 'NZD/JPY'
        ]
        
        self.all_pairs = self.major_pairs + self.cross_pairs
        
        # Event impact coefficients by category and currency importance
        self.impact_coefficients = {
            EventCategory.INTEREST_RATE: {
                'direct': 1.0,
                'major_cross': 0.8,
                'minor_cross': 0.6,
                'commodity': 0.4
            },
            EventCategory.EMPLOYMENT: {
                'direct': 0.9,
                'major_cross': 0.7,
                'minor_cross': 0.5,
                'commodity': 0.3
            },
            EventCategory.INFLATION: {
                'direct': 0.8,
                'major_cross': 0.6,
                'minor_cross': 0.4,
                'commodity': 0.3
            },
            EventCategory.GDP: {
                'direct': 0.7,
                'major_cross': 0.5,
                'minor_cross': 0.3,
                'commodity': 0.2
            },
            EventCategory.PMI: {
                'direct': 0.6,
                'major_cross': 0.4,
                'minor_cross': 0.2,
                'commodity': 0.1
            }
        }
        
        # Risk-on/Risk-off currency classifications
        self.risk_on_currencies = ['AUD', 'NZD', 'CAD', 'EUR', 'GBP']
        self.risk_off_currencies = ['USD', 'JPY', 'CHF']
        
        # Commodity currency relationships
        self.commodity_relationships = {
            'AUD': ['Gold', 'Iron Ore', 'Coal'],
            'CAD': ['Oil', 'Gold'],
            'NZD': ['Dairy', 'Agriculture'],
            'CHF': [],  # Safe haven
            'JPY': []   # Safe haven
        }
    
    def get_currency_from_pair(self, currency_pair: str) -> Tuple[str, str]:
        pair_clean = currency_pair.replace('/', '').replace('_', '')
        return pair_clean[:3], pair_clean[3:]
    
    def calculate_currency_importance(self, currency: str) -> float:
        return self.currency_hierarchy.get(currency, 0.3)
    
    def determine_spillover_type(self, source_currency: str, target_pair: str) -> SpilloverType:
        base_currency, quote_currency = self.get_currency_from_pair(target_pair)
        
        if source_currency in [base_currency, quote_currency]:
            return SpilloverType.DIRECT
        
        # Check for major currency relationships
        major_currencies = ['USD', 'EUR', 'GBP', 'JPY']
        if (source_currency in major_currencies and 
            (base_currency in major_currencies or quote_currency in major_currencies)):
            return SpilloverType.INDIRECT
        
        # Check for risk-on/risk-off relationships
        if ((source_currency in self.risk_on_currencies and 
             base_currency in self.risk_on_currencies) or
            (source_currency in self.risk_off_currencies and 
             base_currency in self.risk_off_currencies)):
            return SpilloverType.RISK_ON_OFF
        
        return SpilloverType.CROSS_CURRENCY
    
    def calculate_spillover_coefficient(self, event: EconomicEvent, target_pair: str) -> float:
        source_currency = event.currency
        base_currency, quote_currency = self.get_currency_from_pair(target_pair)
        
        spillover_type = self.determine_spillover_type(source_currency, target_pair)
        category_coeffs = self.impact_coefficients.get(event.category, 
                                                     self.impact_coefficients[EventCategory.PMI])
        
        # Base coefficient from event category
        if spillover_type == SpilloverType.DIRECT:
            base_coeff = category_coeffs['direct']
        elif spillover_type == SpilloverType.INDIRECT:
            if base_currency in ['EUR', 'GBP', 'JPY'] or quote_currency in ['EUR', 'GBP', 'JPY']:
                base_coeff = category_coeffs['major_cross']
            else:
                base_coeff = category_coeffs['minor_cross']
        elif spillover_type == SpilloverType.RISK_ON_OFF:
            base_coeff = category_coeffs['major_cross'] * 0.7  # Reduced for risk sentiment
        else:  # CROSS_CURRENCY
            base_coeff = category_coeffs['commodity']
        
        # Adjust for currency importance
        source_importance = self.calculate_currency_importance(source_currency)
        target_importance = max(self.calculate_currency_importance(base_currency),
                              self.calculate_currency_importance(quote_currency))
        
        importance_factor = (source_importance + target_importance) / 2
        
        # Adjust for event impact level
        impact_multiplier = {
            EventImpact.LOW: 0.5,
            EventImpact.MEDIUM: 0.75,
            EventImpact.HIGH: 1.0,
            EventImpact.EXTREME: 1.5
        }[event.impact]
        
        final_coefficient = base_coeff * importance_factor * impact_multiplier
        return min(1.0, final_coefficient)
    
    def calculate_transmission_delay(self, event: EconomicEvent, target_pair: str) -> int:
        source_currency = event.currency
        spillover_type = self.determine_spillover_type(source_currency, target_pair)
        
        base_delays = {
            SpilloverType.DIRECT: 0,
            SpilloverType.INDIRECT: 2,
            SpilloverType.RISK_ON_OFF: 5,
            SpilloverType.CROSS_CURRENCY: 10
        }
        
        # Adjust for market liquidity (major pairs react faster)
        if target_pair in self.major_pairs:
            liquidity_factor = 1.0
        else:
            liquidity_factor = 1.5
        
        return int(base_delays[spillover_type] * liquidity_factor)
    
    def calculate_confidence_level(self, event: EconomicEvent, target_pair: str) -> float:
        source_currency = event.currency
        base_currency, quote_currency = self.get_currency_from_pair(target_pair)
        
        # Start with base confidence
        base_confidence = 0.8
        
        # Adjust for spillover type
        spillover_type = self.determine_spillover_type(source_currency, target_pair)
        spillover_confidence = {
            SpilloverType.DIRECT: 1.0,
            SpilloverType.INDIRECT: 0.8,
            SpilloverType.RISK_ON_OFF: 0.6,
            SpilloverType.CROSS_CURRENCY: 0.4
        }[spillover_type]
        
        # Adjust for historical volatility relationships
        if event.category in [EventCategory.INTEREST_RATE, EventCategory.EMPLOYMENT]:
            category_confidence = 0.9
        elif event.category in [EventCategory.INFLATION, EventCategory.GDP]:
            category_confidence = 0.8
        else:
            category_confidence = 0.7
        
        # Adjust for event surprise factor
        surprise_factor = event.get_surprise_factor() if hasattr(event, 'get_surprise_factor') else 0.0
        surprise_confidence = min(1.0, 0.7 + surprise_factor * 0.3)
        
        final_confidence = base_confidence * spillover_confidence * category_confidence * surprise_confidence
        return min(1.0, max(0.1, final_confidence))
    
    def calculate_event_spillovers(self, event: EconomicEvent) -> List[EventSpillover]:
        spillovers = []
        
        for target_pair in self.all_pairs:
            # Skip if the pair doesn't involve the event currency in any meaningful way
            base_currency, quote_currency = self.get_currency_from_pair(target_pair)
            
            # Always include direct relationships
            if event.currency in [base_currency, quote_currency]:
                spillover_coeff = self.calculate_spillover_coefficient(event, target_pair)
                transmission_delay = self.calculate_transmission_delay(event, target_pair)
                confidence = self.calculate_confidence_level(event, target_pair)
                spillover_type = self.determine_spillover_type(event.currency, target_pair)
                
                spillover = EventSpillover(
                    source_event=event,
                    affected_pair=target_pair,
                    spillover_type=spillover_type,
                    impact_coefficient=spillover_coeff,
                    transmission_delay=transmission_delay,
                    confidence_level=confidence
                )
                spillovers.append(spillover)
            
            # Include significant indirect relationships
            elif self.calculate_spillover_coefficient(event, target_pair) > 0.2:
                spillover_coeff = self.calculate_spillover_coefficient(event, target_pair)
                transmission_delay = self.calculate_transmission_delay(event, target_pair)
                confidence = self.calculate_confidence_level(event, target_pair)
                spillover_type = self.determine_spillover_type(event.currency, target_pair)
                
                spillover = EventSpillover(
                    source_event=event,
                    affected_pair=target_pair,
                    spillover_type=spillover_type,
                    impact_coefficient=spillover_coeff,
                    transmission_delay=transmission_delay,
                    confidence_level=confidence
                )
                spillovers.append(spillover)
        
        return sorted(spillovers, key=lambda x: x.get_adjusted_impact(), reverse=True)
    
    def get_simultaneous_impact_pairs(self, event: EconomicEvent, min_impact: float = 0.3) -> List[str]:
        spillovers = self.calculate_event_spillovers(event)
        
        simultaneous_pairs = []
        for spillover in spillovers:
            if spillover.get_adjusted_impact() >= min_impact and spillover.transmission_delay <= 5:
                simultaneous_pairs.append(spillover.affected_pair)
        
        return simultaneous_pairs
    
    def calculate_portfolio_event_impact(self, event: EconomicEvent, 
                                       positions: Dict[str, float]) -> Dict[str, float]:
        spillovers = self.calculate_event_spillovers(event)
        
        portfolio_impacts = {}
        for pair, position_size in positions.items():
            # Find spillover for this pair
            pair_spillover = None
            for spillover in spillovers:
                if spillover.affected_pair == pair:
                    pair_spillover = spillover
                    break
            
            if pair_spillover:
                impact_magnitude = pair_spillover.get_adjusted_impact()
                portfolio_impact = impact_magnitude * abs(position_size)
                portfolio_impacts[pair] = portfolio_impact
            else:
                portfolio_impacts[pair] = 0.0
        
        return portfolio_impacts
    
    def get_optimal_position_adjustments(self, event: EconomicEvent, 
                                       current_positions: Dict[str, float]) -> Dict[str, float]:
        spillovers = self.calculate_event_spillovers(event)
        adjustments = {}
        
        for pair, current_position in current_positions.items():
            # Find spillover for this pair
            pair_spillover = None
            for spillover in spillovers:
                if spillover.affected_pair == pair:
                    pair_spillover = spillover
                    break
            
            if pair_spillover:
                impact = pair_spillover.get_adjusted_impact()
                
                # Calculate adjustment factor based on impact and event type
                if event.impact == EventImpact.EXTREME:
                    adjustment_factor = 0.2  # Reduce to 20% of current position
                elif event.impact == EventImpact.HIGH:
                    adjustment_factor = 0.5  # Reduce to 50% of current position
                elif impact > 0.7:
                    adjustment_factor = 0.6  # High spillover impact
                elif impact > 0.4:
                    adjustment_factor = 0.8  # Medium spillover impact
                else:
                    adjustment_factor = 1.0  # No adjustment needed
                
                adjusted_position = current_position * adjustment_factor
                adjustments[pair] = adjusted_position
            else:
                adjustments[pair] = current_position  # No change
        
        return adjustments
    
    def get_risk_concentration_analysis(self, event: EconomicEvent, 
                                      positions: Dict[str, float]) -> Dict[str, any]:
        spillovers = self.calculate_event_spillovers(event)
        
        # Calculate total exposure to event currency
        total_exposure = 0.0
        affected_pairs = []
        
        for pair, position in positions.items():
            for spillover in spillovers:
                if spillover.affected_pair == pair and spillover.get_adjusted_impact() > 0.2:
                    total_exposure += abs(position) * spillover.get_adjusted_impact()
                    affected_pairs.append((pair, spillover.get_adjusted_impact()))
                    break
        
        # Risk concentration categories
        if total_exposure > 2.0:
            risk_level = "EXTREME"
        elif total_exposure > 1.5:
            risk_level = "HIGH"
        elif total_exposure > 1.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            'event': event.name,
            'event_currency': event.currency,
            'total_exposure': total_exposure,
            'risk_level': risk_level,
            'affected_pairs': affected_pairs,
            'concentration_ratio': total_exposure / sum(abs(p) for p in positions.values()) if positions and sum(abs(p) for p in positions.values()) > 0 else 0,
            'recommendations': self._get_risk_recommendations(risk_level, total_exposure)
        }
    
    def _get_risk_recommendations(self, risk_level: str, total_exposure: float) -> List[str]:
        recommendations = []
        
        if risk_level == "EXTREME":
            recommendations.extend([
                "Immediately reduce positions in affected pairs by 70-80%",
                "Consider flat positions before event if possible",
                "Implement emergency exit strategy",
                "Diversify into non-correlated assets"
            ])
        elif risk_level == "HIGH":
            recommendations.extend([
                "Reduce positions in affected pairs by 40-60%",
                "Widen stop losses significantly",
                "Monitor for early exit opportunities",
                "Avoid new positions in correlated pairs"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "Reduce positions in affected pairs by 20-30%",
                "Adjust stop losses for increased volatility",
                "Monitor event outcome closely"
            ])
        else:
            recommendations.append("Current exposure levels acceptable, maintain monitoring")
        
        return recommendations
    
    def get_event_impact_summary(self, event: EconomicEvent, 
                               positions: Dict[str, float] = None) -> Dict[str, any]:
        spillovers = self.calculate_event_spillovers(event)
        
        # Group spillovers by type
        spillover_by_type = {}
        for spillover in spillovers:
            spillover_type = spillover.spillover_type.value
            if spillover_type not in spillover_by_type:
                spillover_by_type[spillover_type] = []
            spillover_by_type[spillover_type].append({
                'pair': spillover.affected_pair,
                'impact': spillover.get_adjusted_impact(),
                'delay': spillover.transmission_delay
            })
        
        summary = {
            'event_name': event.name,
            'event_currency': event.currency,
            'event_impact': event.impact.value,
            'event_category': event.category.value,
            'total_affected_pairs': len(spillovers),
            'spillover_breakdown': spillover_by_type,
            'high_impact_pairs': [s.affected_pair for s in spillovers if s.get_adjusted_impact() > 0.6],
            'simultaneous_impact_pairs': self.get_simultaneous_impact_pairs(event),
            'max_spillover_impact': max([s.get_adjusted_impact() for s in spillovers]) if spillovers else 0.0
        }
        
        if positions:
            portfolio_impacts = self.calculate_portfolio_event_impact(event, positions)
            risk_analysis = self.get_risk_concentration_analysis(event, positions)
            optimal_adjustments = self.get_optimal_position_adjustments(event, positions)
            
            summary.update({
                'portfolio_impacts': portfolio_impacts,
                'risk_concentration': risk_analysis,
                'recommended_adjustments': optimal_adjustments
            })
        
        return summary