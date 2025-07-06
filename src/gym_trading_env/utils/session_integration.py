import datetime
import pytz
from typing import Dict, Any, Optional
from session_manager import SessionManager


class SessionIntegration:
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.session_manager = session_manager or SessionManager()
    
    def add_session_features(self, df, timestamp_column: str = None):
        if timestamp_column is None:
            timestamps = df.index
        else:
            timestamps = df[timestamp_column]
        
        session_features = {}
        
        for timestamp in timestamps:
            if isinstance(timestamp, str):
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            
            session_info = self.session_manager.get_session_info(dt)
            
            if 'feature_session_liquidity' not in session_features:
                session_features['feature_session_liquidity'] = []
            if 'feature_session_volatility' not in session_features:
                session_features['feature_session_volatility'] = []
            if 'feature_session_overlap' not in session_features:
                session_features['feature_session_overlap'] = []
            if 'feature_session_holiday_risk' not in session_features:
                session_features['feature_session_holiday_risk'] = []
            if 'feature_session_position_multiplier' not in session_features:
                session_features['feature_session_position_multiplier'] = []
            
            session_features['feature_session_liquidity'].append(session_info['liquidity_score'])
            session_features['feature_session_volatility'].append(session_info['volatility_multiplier'])
            session_features['feature_session_overlap'].append(1.0 if session_info['is_london_ny_overlap'] else 0.0)
            session_features['feature_session_holiday_risk'].append(1.0 - session_info['holiday_adjusted_liquidity'])
            session_features['feature_session_position_multiplier'].append(self.session_manager.get_position_size_multiplier(dt))
        
        for feature_name, values in session_features.items():
            df[feature_name] = values
        
        return df
    
    def get_session_adjusted_position_size(self, timestamp, base_position_size: float) -> float:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        multiplier = self.session_manager.get_position_size_multiplier(dt)
        return base_position_size * multiplier
    
    def should_restrict_trading(self, timestamp) -> bool:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        return self.session_manager.should_avoid_trading(dt)
    
    def get_session_context(self, timestamp) -> Dict[str, Any]:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        return self.session_manager.get_session_info(dt)
    
    def get_dynamic_session_features(self, timestamp) -> Dict[str, float]:
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        session_info = self.session_manager.get_session_info(dt)
        
        return {
            'liquidity_score': session_info['liquidity_score'],
            'volatility_multiplier': session_info['volatility_multiplier'],
            'london_ny_overlap': 1.0 if session_info['is_london_ny_overlap'] else 0.0,
            'holiday_risk': 1.0 - session_info['holiday_adjusted_liquidity'],
            'position_multiplier': self.session_manager.get_position_size_multiplier(dt),
            'trading_restriction': 1.0 if self.session_manager.should_avoid_trading(dt) else 0.0
        }


def dynamic_feature_session_liquidity(history):
    integration = SessionIntegration()
    current_timestamp = history.df.index[history._idx]
    features = integration.get_dynamic_session_features(current_timestamp)
    return features['liquidity_score']


def dynamic_feature_session_volatility(history):
    integration = SessionIntegration()
    current_timestamp = history.df.index[history._idx]
    features = integration.get_dynamic_session_features(current_timestamp)
    return features['volatility_multiplier']


def dynamic_feature_london_ny_overlap(history):
    integration = SessionIntegration()
    current_timestamp = history.df.index[history._idx]
    features = integration.get_dynamic_session_features(current_timestamp)
    return features['london_ny_overlap']


def dynamic_feature_holiday_risk(history):
    integration = SessionIntegration()
    current_timestamp = history.df.index[history._idx]
    features = integration.get_dynamic_session_features(current_timestamp)
    return features['holiday_risk']


def dynamic_feature_position_multiplier(history):
    integration = SessionIntegration()
    current_timestamp = history.df.index[history._idx]
    features = integration.get_dynamic_session_features(current_timestamp)
    return features['position_multiplier']