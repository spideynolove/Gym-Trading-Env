import datetime
import pytz
from typing import Dict, Any, Optional, List
from .news_risk_manager import NewsRiskManager
from .economic_calendar_api import EconomicCalendarAPI


class NewsRiskIntegration:
    
    def __init__(self, news_risk_manager: Optional[NewsRiskManager] = None, 
                 calendar_api: Optional[EconomicCalendarAPI] = None):
        self.news_risk_manager = news_risk_manager or NewsRiskManager()
        self.calendar_api = calendar_api or EconomicCalendarAPI()
        
        # Load events from API if not already loaded
        if len(self.news_risk_manager.events) <= 5:  # Only sample events
            self._load_calendar_events()
    
    def _load_calendar_events(self):
        try:
            events = self.calendar_api.fetch_calendar_data('sample')
            for event in events:
                self.news_risk_manager.add_event(event)
        except Exception as e:
            print(f"Warning: Could not load calendar events - {e}")
    
    def get_news_adjusted_position_size(self, timestamp, currency_pair: str, base_position_size: float) -> float:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        multiplier = self.news_risk_manager.get_position_size_multiplier(dt, currency_pair)
        return base_position_size * multiplier
    
    def get_news_adjusted_stop_loss(self, timestamp, currency_pair: str, base_stop_distance: float) -> float:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        multiplier = self.news_risk_manager.get_stop_loss_multiplier(dt, currency_pair)
        return base_stop_distance * multiplier
    
    def should_restrict_trading(self, timestamp, currency_pair: str) -> bool:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        return self.news_risk_manager.should_avoid_trading(dt, currency_pair)
    
    def get_emergency_exit_level(self, timestamp) -> float:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        return self.news_risk_manager.get_emergency_exit_threshold(dt)
    
    def get_volatility_forecast(self, timestamp, currency_pair: str) -> float:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        return self.news_risk_manager.get_volatility_forecast(dt, currency_pair)
    
    def get_news_context(self, timestamp, currency_pair: str) -> Dict[str, Any]:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        return self.news_risk_manager.get_risk_assessment(dt, currency_pair)
    
    def get_dynamic_news_features(self, timestamp, currency_pair: str) -> Dict[str, float]:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        assessment = self.news_risk_manager.get_risk_assessment(dt, currency_pair)
        
        return {
            'position_size_multiplier': assessment['position_size_multiplier'],
            'stop_loss_multiplier': assessment['stop_loss_multiplier'],
            'trading_restriction': 1.0 if assessment['should_avoid_trading'] else 0.0,
            'emergency_exit_threshold': assessment['emergency_exit_threshold'],
            'volatility_forecast': assessment['volatility_forecast'],
            'event_period_indicator': 1.0 if assessment['is_event_period'] else 0.0,
            'minutes_to_next_event': assessment['minutes_to_next_event'] or 1440.0  # Default 24 hours
        }
    
    def add_news_features_to_dataframe(self, df, currency_pair: str, timestamp_column: str = None):
        if timestamp_column is None:
            timestamps = df.index
        else:
            timestamps = df[timestamp_column]
        
        news_features = {}
        
        for timestamp in timestamps:
            if isinstance(timestamp, str):
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            
            features = self.get_dynamic_news_features(dt, currency_pair)
            
            for feature_name, value in features.items():
                if f'feature_news_{feature_name}' not in news_features:
                    news_features[f'feature_news_{feature_name}'] = []
                news_features[f'feature_news_{feature_name}'].append(value)
        
        for feature_name, values in news_features.items():
            df[feature_name] = values
        
        return df
    
    def update_events_with_actual_values(self, event_outcomes: Dict[str, float]):
        for event_name, actual_value in event_outcomes.items():
            self.news_risk_manager.update_event_outcome(event_name, actual_value)
    
    def get_upcoming_events_summary(self, timestamp, currency_pair: str, hours_ahead: int = 72) -> List[Dict]:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        upcoming_events = self.news_risk_manager.get_upcoming_events(dt, hours_ahead)
        
        relevant_events = []
        for event in upcoming_events:
            if self.news_risk_manager._event_affects_pair(event, currency_pair):
                event_summary = {
                    'name': event.name,
                    'timestamp': event.timestamp,
                    'currency': event.currency,
                    'impact': event.impact.value,
                    'category': event.category.value,
                    'hours_until': (event.timestamp - dt).total_seconds() / 3600,
                    'forecast': event.forecast_value,
                    'previous': event.previous_value
                }
                relevant_events.append(event_summary)
        
        return relevant_events


def dynamic_feature_news_position_multiplier(history):
    integration = NewsRiskIntegration()
    current_timestamp = history.df.index[history._idx]
    
    # Assume EUR/USD as default, should be parameterized in real implementation
    currency_pair = "EUR/USD"
    features = integration.get_dynamic_news_features(current_timestamp, currency_pair)
    return features['position_size_multiplier']


def dynamic_feature_news_stop_multiplier(history):
    integration = NewsRiskIntegration()
    current_timestamp = history.df.index[history._idx]
    
    currency_pair = "EUR/USD"
    features = integration.get_dynamic_news_features(current_timestamp, currency_pair)
    return features['stop_loss_multiplier']


def dynamic_feature_news_trading_restriction(history):
    integration = NewsRiskIntegration()
    current_timestamp = history.df.index[history._idx]
    
    currency_pair = "EUR/USD"
    features = integration.get_dynamic_news_features(current_timestamp, currency_pair)
    return features['trading_restriction']


def dynamic_feature_news_volatility_forecast(history):
    integration = NewsRiskIntegration()
    current_timestamp = history.df.index[history._idx]
    
    currency_pair = "EUR/USD"
    features = integration.get_dynamic_news_features(current_timestamp, currency_pair)
    return features['volatility_forecast']


def dynamic_feature_news_event_indicator(history):
    integration = NewsRiskIntegration()
    current_timestamp = history.df.index[history._idx]
    
    currency_pair = "EUR/USD"
    features = integration.get_dynamic_news_features(current_timestamp, currency_pair)
    return features['event_period_indicator']