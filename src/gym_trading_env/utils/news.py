import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from pathlib import Path

class NewsManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "news_events.json"
        
        self.config = self._load_config(config_path)
        self.news_events = None
        self.filtered_periods = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "high_impact_events": [],
                "high_volatility_keywords": [],
                "volatility_levels": {"high": [], "moderate": [], "low": []},
                "buffer_settings": {"high_impact_minutes": 30, "moderate_impact_minutes": 15, "low_impact_minutes": 5}
            }
    
    def load_economic_calendar(self, calendar_data: pd.DataFrame) -> None:
        if not isinstance(calendar_data, pd.DataFrame):
            raise ValueError("Calendar data must be a pandas DataFrame")
        
        required_columns = ['Date', 'Time_NY', 'Volatility', 'Event_Description']
        missing_columns = [col for col in required_columns if col not in calendar_data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        self.news_events = calendar_data.copy()
        self.news_events['datetime'] = pd.to_datetime(
            self.news_events['Date'] + ' ' + self.news_events['Time_NY']
        )
        self.news_events = self.news_events.sort_values('datetime')
        self._build_filtered_periods()
    
    def _get_event_impact_level(self, event_row: pd.Series) -> str:
        event_desc = str(event_row['Event_Description']).strip()
        volatility = str(event_row['Volatility']).strip()
        
        for level, patterns in self.config['volatility_levels'].items():
            if any(pattern in volatility for pattern in patterns):
                return level
        
        for high_impact in self.config['high_impact_events']:
            if high_impact.lower() in event_desc.lower():
                return 'high'
        
        for keyword in self.config['high_volatility_keywords']:
            if keyword.lower() in event_desc.lower():
                return 'moderate'
        
        return 'low'
    
    def _build_filtered_periods(self) -> None:
        self.filtered_periods = {'high': set(), 'moderate': set(), 'low': set()}
        
        if self.news_events is None:
            return
        
        for _, event in self.news_events.iterrows():
            impact_level = self._get_event_impact_level(event)
            buffer_minutes = self.config['buffer_settings'].get(f'{impact_level}_impact_minutes', 15)
            
            event_time = event['datetime']
            start_time = event_time - timedelta(minutes=buffer_minutes)
            end_time = event_time + timedelta(minutes=buffer_minutes)
            
            current_time = start_time
            while current_time <= end_time:
                self.filtered_periods[impact_level].add(current_time.floor('min'))
                current_time += timedelta(minutes=1)
    
    def should_avoid_trading(self, timestamp: pd.Timestamp, impact_levels: List[str] = ['high']) -> bool:
        if not self.filtered_periods:
            return False
        
        check_time = timestamp.floor('min')
        
        for level in impact_levels:
            if check_time in self.filtered_periods.get(level, set()):
                return True
        
        return False
    
    def get_next_news_event(self, timestamp: pd.Timestamp, impact_levels: List[str] = ['high']) -> Optional[Dict]:
        if self.news_events is None:
            return None
        
        upcoming_events = self.news_events[self.news_events['datetime'] > timestamp].copy()
        
        if upcoming_events.empty:
            return None
        
        filtered_events = []
        for _, event in upcoming_events.iterrows():
            if self._get_event_impact_level(event) in impact_levels:
                filtered_events.append(event)
        
        if not filtered_events:
            return None
        
        next_event = filtered_events[0]
        return {
            'datetime': next_event['datetime'],
            'description': next_event['Event_Description'],
            'volatility': next_event['Volatility'],
            'country': next_event.get('Country', ''),
            'impact_level': self._get_event_impact_level(next_event),
            'minutes_until': (next_event['datetime'] - timestamp).total_seconds() / 60
        }
    
    def filter_trading_data(self, df: pd.DataFrame, timestamp_col: str = 'timestamp', 
                           impact_levels: List[str] = ['high']) -> pd.DataFrame:
        if self.news_events is None:
            return df
        
        df_result = df.copy()
        
        if timestamp_col not in df_result.columns:
            df_result[timestamp_col] = pd.to_datetime(df_result.index)
        
        df_result['news_filter'] = df_result[timestamp_col].apply(
            lambda x: not self.should_avoid_trading(x, impact_levels)
        )
        
        return df_result[df_result['news_filter']].drop(columns=['news_filter'])
    
    def add_news_features(self, df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
        if self.news_events is None:
            return df
        
        df_result = df.copy()
        
        if timestamp_col not in df_result.columns:
            df_result[timestamp_col] = pd.to_datetime(df_result.index)
        
        df_result['avoid_high_impact'] = df_result[timestamp_col].apply(
            lambda x: self.should_avoid_trading(x, ['high'])
        )
        df_result['avoid_moderate_impact'] = df_result[timestamp_col].apply(
            lambda x: self.should_avoid_trading(x, ['moderate'])
        )
        
        news_info = df_result[timestamp_col].apply(
            lambda x: self.get_next_news_event(x, ['high', 'moderate'])
        )
        
        df_result['next_news_minutes'] = news_info.apply(
            lambda x: x['minutes_until'] if x else 999
        )
        df_result['next_news_impact'] = news_info.apply(
            lambda x: x['impact_level'] if x else 'none'
        )
        
        return df_result

def news_volatility_flag(news_time: datetime, current_time: datetime, buffer_min: int = 15) -> int:
    time_diff = (news_time - current_time).total_seconds() / 60
    return 1 if 0 <= time_diff <= buffer_min else 0

def load_economic_calendar_csv(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        raise ValueError(f"Failed to load economic calendar: {e}")

def create_news_manager_from_csv(filepath: str, config_path: str = None) -> NewsManager:
    calendar_data = load_economic_calendar_csv(filepath)
    news_manager = NewsManager(config_path=config_path)
    news_manager.load_economic_calendar(calendar_data)
    return news_manager

def filter_high_impact_events(df: pd.DataFrame, economic_calendar: pd.DataFrame, 
                             impact_levels: List[str] = ['high']) -> pd.DataFrame:
    news_manager = NewsManager()
    news_manager.load_economic_calendar(economic_calendar)
    return news_manager.filter_trading_data(df, impact_levels=impact_levels)

def adjust_lot_size_for_news(pre_news_spread: float, baseline_spread: float, 
                           max_reduction: float = 0.1) -> float:
    if baseline_spread == 0:
        return max_reduction
    
    multiplier = baseline_spread / pre_news_spread
    return max(max_reduction, multiplier)