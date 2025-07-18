import pandas as pd
from datetime import datetime
from typing import Dict, Tuple

class SessionManager:
    SESSION_TIMES = {
        'tokyo': (0, 9),
        'london': (8, 15),
        'new_york': (13, 22),
        'sydney': (21, 6)
    }
    
    SPREAD_MULTIPLIERS = {
        'asian': 2.5,
        'london_ny_overlap': 0.75,
        'london': 1.2,
        'new_york': 1.0,
        'sydney': 1.8,
        'quiet': 3.0
    }
    
    def __init__(self):
        self.current_session = None
        self.current_multiplier = 1.0
    
    def detect_session(self, timestamp: pd.Timestamp) -> str:
        if timestamp.tz is None:
            hour = timestamp.hour
        else:
            hour = timestamp.tz_convert('UTC').hour
        
        active_sessions = []
        
        for session, (start, end) in self.SESSION_TIMES.items():
            if start <= end:
                if start <= hour < end:
                    active_sessions.append(session)
            else:
                if hour >= start or hour < end:
                    active_sessions.append(session)
        
        if 'london' in active_sessions and 'new_york' in active_sessions:
            return 'london_ny_overlap'
        elif 'tokyo' in active_sessions and 'sydney' in active_sessions:
            return 'asian'
        elif 'london' in active_sessions:
            return 'london'
        elif 'new_york' in active_sessions:
            return 'new_york'
        elif 'sydney' in active_sessions or 'tokyo' in active_sessions:
            return 'asian'
        else:
            return 'quiet'
    
    def get_spread_multiplier(self, timestamp: pd.Timestamp) -> float:
        session = self.detect_session(timestamp)
        return self.SPREAD_MULTIPLIERS.get(session, 1.0)
    
    def get_current_spread(self, timestamp: pd.Timestamp, base_spread: float = 0.0001) -> float:
        multiplier = self.get_spread_multiplier(timestamp)
        return base_spread * multiplier
    
    def is_high_volatility_session(self, timestamp: pd.Timestamp) -> bool:
        session = self.detect_session(timestamp)
        return session in ['london_ny_overlap', 'london', 'new_york']
    
    def get_session_info(self, timestamp: pd.Timestamp) -> Dict:
        session = self.detect_session(timestamp)
        multiplier = self.get_spread_multiplier(timestamp)
        
        return {
            'session': session,
            'spread_multiplier': multiplier,
            'high_volatility': self.is_high_volatility_session(timestamp),
            'hour_utc': timestamp.tz_convert('UTC').hour if timestamp.tz else timestamp.hour
        }

def add_session_features(df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
    session_mgr = SessionManager()
    df_result = df.copy()
    
    if timestamp_col not in df_result.columns:
        df_result[timestamp_col] = pd.to_datetime(df_result.index)
    
    df_result['session'] = df_result[timestamp_col].apply(session_mgr.detect_session)
    df_result['spread_multiplier'] = df_result[timestamp_col].apply(session_mgr.get_spread_multiplier)
    df_result['high_volatility_session'] = df_result[timestamp_col].apply(session_mgr.is_high_volatility_session)
    
    df_result['hour_utc'] = df_result[timestamp_col].dt.tz_convert('UTC').dt.hour if df_result[timestamp_col].dt.tz else df_result[timestamp_col].dt.hour
    df_result['london_ny_overlap'] = ((df_result['hour_utc'] >= 13) & (df_result['hour_utc'] < 15)).astype(int)
    df_result['asian_session'] = (((df_result['hour_utc'] >= 21) & (df_result['hour_utc'] < 24)) | 
                                 ((df_result['hour_utc'] >= 0) & (df_result['hour_utc'] < 9))).astype(int)
    
    return df_result

def calculate_dynamic_spread(price: float, base_spread: float, session_multiplier: float) -> float:
    return base_spread * session_multiplier

def session_volatility_score(pair: str, hour: int) -> float:
    if any(curr in pair.upper() for curr in ['JPY', 'AUD', 'NZD']):
        return 1.0 if (hour >= 21) or (hour < 6) else 0.3
    elif any(curr in pair.upper() for curr in ['GBP', 'EUR', 'CHF']):
        return 1.0 if (hour >= 7) and (hour < 16) else 0.3
    elif any(curr in pair.upper() for curr in ['USD', 'CAD']):
        return 1.0 if (hour >= 12) and (hour < 21) else 0.3
    return 0.5