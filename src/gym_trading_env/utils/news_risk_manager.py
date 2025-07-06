import datetime
import pytz
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class EventImpact(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    EXTREME = "Extreme"


class EventCategory(Enum):
    INTEREST_RATE = "Interest Rate"
    EMPLOYMENT = "Employment"
    INFLATION = "Inflation"
    GDP = "GDP"
    PMI = "PMI"
    RETAIL_SALES = "Retail Sales"
    TRADE_BALANCE = "Trade Balance"
    CENTRAL_BANK = "Central Bank"
    GEOPOLITICAL = "Geopolitical"


@dataclass
class EconomicEvent:
    timestamp: datetime.datetime
    name: str
    currency: str
    impact: EventImpact
    category: EventCategory
    actual_value: Optional[float] = None
    forecast_value: Optional[float] = None
    previous_value: Optional[float] = None
    description: str = ""
    
    def get_surprise_factor(self) -> float:
        if self.actual_value is None or self.forecast_value is None:
            return 0.0
        
        if self.forecast_value == 0:
            return 0.0
        
        return abs((self.actual_value - self.forecast_value) / self.forecast_value)
    
    def is_high_impact(self) -> bool:
        return self.impact in [EventImpact.HIGH, EventImpact.EXTREME]


class NewsRiskManager:
    
    def __init__(self):
        self.events: List[EconomicEvent] = []
        self.impact_multipliers = {
            EventImpact.LOW: 1.0,
            EventImpact.MEDIUM: 1.5,
            EventImpact.HIGH: 2.5,
            EventImpact.EXTREME: 4.0
        }
        
        self.pre_event_windows = {
            EventImpact.LOW: 15,      # 15 minutes before
            EventImpact.MEDIUM: 30,   # 30 minutes before
            EventImpact.HIGH: 60,     # 1 hour before
            EventImpact.EXTREME: 120  # 2 hours before
        }
        
        self.post_event_windows = {
            EventImpact.LOW: 30,      # 30 minutes after
            EventImpact.MEDIUM: 60,   # 1 hour after
            EventImpact.HIGH: 120,    # 2 hours after
            EventImpact.EXTREME: 240  # 4 hours after
        }
        
        self.position_reduction_factors = {
            EventImpact.LOW: 1.0,     # No reduction
            EventImpact.MEDIUM: 0.8,  # 20% reduction
            EventImpact.HIGH: 0.5,    # 50% reduction
            EventImpact.EXTREME: 0.0  # Full exit
        }
        
        self.stop_loss_multipliers = {
            EventImpact.LOW: 1.0,     # Normal stops
            EventImpact.MEDIUM: 1.5,  # 1.5x wider
            EventImpact.HIGH: 2.5,    # 2.5x wider
            EventImpact.EXTREME: 3.0  # 3x wider
        }
        
        self._initialize_sample_events()
    
    def _initialize_sample_events(self):
        base_date = datetime.datetime(2024, 1, 15, tzinfo=pytz.UTC)
        
        sample_events = [
            EconomicEvent(
                timestamp=base_date.replace(hour=13, minute=30),
                name="Non-Farm Payrolls",
                currency="USD",
                impact=EventImpact.HIGH,
                category=EventCategory.EMPLOYMENT,
                forecast_value=180000,
                previous_value=199000,
                description="US monthly employment change"
            ),
            EconomicEvent(
                timestamp=base_date.replace(hour=14, minute=0),
                name="Federal Reserve Interest Rate Decision",
                currency="USD",
                impact=EventImpact.EXTREME,
                category=EventCategory.INTEREST_RATE,
                forecast_value=5.25,
                previous_value=5.00,
                description="Federal Reserve monetary policy decision"
            ),
            EconomicEvent(
                timestamp=base_date.replace(hour=9, minute=30),
                name="UK CPI Year over Year",
                currency="GBP",
                impact=EventImpact.HIGH,
                category=EventCategory.INFLATION,
                forecast_value=4.2,
                previous_value=4.6,
                description="UK annual inflation rate"
            ),
            EconomicEvent(
                timestamp=base_date.replace(hour=1, minute=30),
                name="Japan Core CPI",
                currency="JPY",
                impact=EventImpact.MEDIUM,
                category=EventCategory.INFLATION,
                forecast_value=2.8,
                previous_value=2.9,
                description="Japan core consumer price index"
            ),
            EconomicEvent(
                timestamp=base_date.replace(hour=15, minute=0),
                name="US Retail Sales",
                currency="USD",
                impact=EventImpact.MEDIUM,
                category=EventCategory.RETAIL_SALES,
                forecast_value=0.3,
                previous_value=0.6,
                description="US monthly retail sales change"
            )
        ]
        
        self.events.extend(sample_events)
    
    def add_event(self, event: EconomicEvent):
        self.events.append(event)
        self.events.sort(key=lambda e: e.timestamp)
    
    def get_events_in_timeframe(self, start_time: datetime.datetime, end_time: datetime.datetime) -> List[EconomicEvent]:
        return [event for event in self.events 
                if start_time <= event.timestamp <= end_time]
    
    def get_upcoming_events(self, current_time: datetime.datetime, hours_ahead: int = 24) -> List[EconomicEvent]:
        end_time = current_time + datetime.timedelta(hours=hours_ahead)
        return [event for event in self.events 
                if current_time <= event.timestamp <= end_time]
    
    def get_next_high_impact_event(self, current_time: datetime.datetime) -> Optional[EconomicEvent]:
        upcoming = self.get_upcoming_events(current_time, hours_ahead=168)  # Next week
        high_impact = [e for e in upcoming if e.is_high_impact()]
        return high_impact[0] if high_impact else None
    
    def is_pre_event_period(self, current_time: datetime.datetime) -> Tuple[bool, Optional[EconomicEvent]]:
        for event in self.events:
            window_minutes = self.pre_event_windows[event.impact]
            pre_event_start = event.timestamp - datetime.timedelta(minutes=window_minutes)
            
            if pre_event_start <= current_time <= event.timestamp:
                return True, event
        
        return False, None
    
    def is_post_event_period(self, current_time: datetime.datetime) -> Tuple[bool, Optional[EconomicEvent]]:
        for event in self.events:
            window_minutes = self.post_event_windows[event.impact]
            post_event_end = event.timestamp + datetime.timedelta(minutes=window_minutes)
            
            if event.timestamp <= current_time <= post_event_end:
                return True, event
        
        return False, None
    
    def is_event_period(self, current_time: datetime.datetime) -> Tuple[bool, Optional[EconomicEvent], str]:
        is_pre, pre_event = self.is_pre_event_period(current_time)
        if is_pre:
            return True, pre_event, "pre_event"
        
        is_post, post_event = self.is_post_event_period(current_time)
        if is_post:
            return True, post_event, "post_event"
        
        return False, None, "normal"
    
    def get_position_size_multiplier(self, current_time: datetime.datetime, currency_pair: str) -> float:
        is_event, event, period = self.is_event_period(current_time)
        
        if not is_event:
            return 1.0
        
        if not self._event_affects_pair(event, currency_pair):
            return 1.0
        
        return self.position_reduction_factors[event.impact]
    
    def get_stop_loss_multiplier(self, current_time: datetime.datetime, currency_pair: str) -> float:
        is_event, event, period = self.is_event_period(current_time)
        
        if not is_event:
            return 1.0
        
        if not self._event_affects_pair(event, currency_pair):
            return 1.0
        
        return self.stop_loss_multipliers[event.impact]
    
    def _event_affects_pair(self, event: EconomicEvent, currency_pair: str) -> bool:
        event_currency = event.currency
        pair_currencies = currency_pair.replace('/', '').replace('_', '')
        
        return event_currency in pair_currencies
    
    def should_avoid_trading(self, current_time: datetime.datetime, currency_pair: str) -> bool:
        is_event, event, period = self.is_event_period(current_time)
        
        if not is_event:
            return False
        
        if not self._event_affects_pair(event, currency_pair):
            return False
        
        if event.impact == EventImpact.EXTREME:
            return True
        
        next_high_impact = self.get_next_high_impact_event(current_time)
        if next_high_impact:
            time_to_event = (next_high_impact.timestamp - current_time).total_seconds() / 60
            if time_to_event <= 30 and next_high_impact.impact == EventImpact.EXTREME:
                return True
        
        return False
    
    def get_emergency_exit_threshold(self, current_time: datetime.datetime) -> float:
        is_event, event, period = self.is_event_period(current_time)
        
        if not is_event:
            return 0.05  # 5% normal threshold
        
        thresholds = {
            EventImpact.LOW: 0.03,     # 3%
            EventImpact.MEDIUM: 0.02,  # 2%
            EventImpact.HIGH: 0.015,   # 1.5%
            EventImpact.EXTREME: 0.01  # 1%
        }
        
        return thresholds[event.impact]
    
    def get_volatility_forecast(self, current_time: datetime.datetime, currency_pair: str) -> float:
        base_volatility = 1.0
        
        upcoming_events = self.get_upcoming_events(current_time, hours_ahead=4)
        affected_events = [e for e in upcoming_events if self._event_affects_pair(e, currency_pair)]
        
        if not affected_events:
            return base_volatility
        
        max_impact = max(self.impact_multipliers[e.impact] for e in affected_events)
        return base_volatility * max_impact
    
    def get_risk_assessment(self, current_time: datetime.datetime, currency_pair: str) -> Dict:
        is_event, event, period = self.is_event_period(current_time)
        
        assessment = {
            'timestamp': current_time,
            'currency_pair': currency_pair,
            'is_event_period': is_event,
            'event_period_type': period,
            'affected_event': event.name if event else None,
            'event_impact': event.impact.value if event else None,
            'position_size_multiplier': self.get_position_size_multiplier(current_time, currency_pair),
            'stop_loss_multiplier': self.get_stop_loss_multiplier(current_time, currency_pair),
            'should_avoid_trading': self.should_avoid_trading(current_time, currency_pair),
            'emergency_exit_threshold': self.get_emergency_exit_threshold(current_time),
            'volatility_forecast': self.get_volatility_forecast(current_time, currency_pair),
            'next_high_impact_event': None,
            'minutes_to_next_event': None
        }
        
        next_event = self.get_next_high_impact_event(current_time)
        if next_event:
            assessment['next_high_impact_event'] = next_event.name
            assessment['minutes_to_next_event'] = (next_event.timestamp - current_time).total_seconds() / 60
        
        return assessment
    
    def update_event_outcome(self, event_name: str, actual_value: float):
        for event in self.events:
            if event.name == event_name:
                event.actual_value = actual_value
                break
    
    def get_event_impact_score(self, event: EconomicEvent) -> float:
        base_score = self.impact_multipliers[event.impact]
        surprise_factor = event.get_surprise_factor()
        
        return base_score * (1 + surprise_factor)
    
    def get_currency_specific_events(self, currency: str, hours_ahead: int = 24) -> List[EconomicEvent]:
        current_time = datetime.datetime.now(pytz.UTC)
        upcoming = self.get_upcoming_events(current_time, hours_ahead)
        return [e for e in upcoming if e.currency == currency]