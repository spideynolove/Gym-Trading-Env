import datetime
import pytz
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class MarketSession(Enum):
    SYDNEY = "Sydney"
    TOKYO = "Tokyo"
    LONDON = "London"
    NEW_YORK = "New York"


@dataclass
class SessionInfo:
    name: str
    start_hour: int
    end_hour: int
    timezone: str
    major_pairs: Set[str]
    volatility_multiplier: float
    liquidity_score: float


class SessionManager:
    def __init__(self):
        self.sessions = {
            MarketSession.SYDNEY: SessionInfo(
                name="Sydney",
                start_hour=21,
                end_hour=6,
                timezone="Australia/Sydney",
                major_pairs={"AUD/USD", "NZD/USD", "AUD/JPY", "NZD/JPY"},
                volatility_multiplier=0.6,
                liquidity_score=0.3
            ),
            MarketSession.TOKYO: SessionInfo(
                name="Tokyo",
                start_hour=0,
                end_hour=9,
                timezone="Asia/Tokyo",
                major_pairs={"USD/JPY", "EUR/JPY", "GBP/JPY", "AUD/JPY", "NZD/JPY"},
                volatility_multiplier=0.7,
                liquidity_score=0.4
            ),
            MarketSession.LONDON: SessionInfo(
                name="London",
                start_hour=8,
                end_hour=17,
                timezone="Europe/London",
                major_pairs={"EUR/USD", "GBP/USD", "USD/CHF", "EUR/GBP", "EUR/CHF", "GBP/CHF"},
                volatility_multiplier=1.2,
                liquidity_score=0.8
            ),
            MarketSession.NEW_YORK: SessionInfo(
                name="New York",
                start_hour=13,
                end_hour=22,
                timezone="America/New_York",
                major_pairs={"EUR/USD", "GBP/USD", "USD/CAD", "USD/CHF", "USD/JPY"},
                volatility_multiplier=1.1,
                liquidity_score=0.7
            )
        }
        
        self.holidays = {
            'UK': [
                '2024-01-01', '2024-03-29', '2024-04-01', '2024-05-06', '2024-05-27',
                '2024-08-26', '2024-12-25', '2024-12-26',
                '2025-01-01', '2025-04-18', '2025-04-21', '2025-05-05', '2025-05-26',
                '2025-08-25', '2025-12-25', '2025-12-26'
            ],
            'US': [
                '2024-01-01', '2024-01-15', '2024-02-19', '2024-05-27', '2024-06-19',
                '2024-07-04', '2024-09-02', '2024-10-14', '2024-11-11', '2024-11-28',
                '2024-12-25', '2025-01-01', '2025-01-20', '2025-02-17', '2025-05-26',
                '2025-06-19', '2025-07-04', '2025-09-01', '2025-10-13', '2025-11-11',
                '2025-11-27', '2025-12-25'
            ],
            'JP': [
                '2024-01-01', '2024-01-08', '2024-02-11', '2024-02-12', '2024-02-23',
                '2024-03-20', '2024-04-29', '2024-05-03', '2024-05-04', '2024-05-05',
                '2024-07-15', '2024-08-11', '2024-08-12', '2024-09-16', '2024-09-23',
                '2024-10-14', '2024-11-03', '2024-11-04', '2024-11-23', '2024-12-31',
                '2025-01-01', '2025-01-13', '2025-02-11', '2025-02-23', '2025-03-20',
                '2025-04-29', '2025-05-03', '2025-05-04', '2025-05-05', '2025-07-21',
                '2025-08-11', '2025-09-15', '2025-09-23', '2025-10-13', '2025-11-03',
                '2025-11-23', '2025-12-23'
            ]
        }
    
    def get_active_sessions(self, dt: datetime.datetime) -> List[MarketSession]:
        gmt_time = dt.astimezone(pytz.UTC)
        gmt_hour = gmt_time.hour
        
        active_sessions = []
        
        for session, info in self.sessions.items():
            if self._is_session_active(gmt_hour, info):
                active_sessions.append(session)
        
        return active_sessions
    
    def _is_session_active(self, gmt_hour: int, session_info: SessionInfo) -> bool:
        start = session_info.start_hour
        end = session_info.end_hour
        
        if start <= end:
            return start <= gmt_hour < end
        else:
            return gmt_hour >= start or gmt_hour < end
    
    def get_session_overlaps(self, dt: datetime.datetime) -> List[Tuple[MarketSession, MarketSession]]:
        active_sessions = self.get_active_sessions(dt)
        overlaps = []
        
        for i in range(len(active_sessions)):
            for j in range(i + 1, len(active_sessions)):
                overlaps.append((active_sessions[i], active_sessions[j]))
        
        return overlaps
    
    def is_london_ny_overlap(self, dt: datetime.datetime) -> bool:
        gmt_time = dt.astimezone(pytz.UTC)
        gmt_hour = gmt_time.hour
        
        return 13 <= gmt_hour < 17
    
    def get_liquidity_score(self, dt: datetime.datetime) -> float:
        active_sessions = self.get_active_sessions(dt)
        
        if not active_sessions:
            return 0.1
        
        if self.is_london_ny_overlap(dt):
            return 1.0
        
        total_liquidity = sum(self.sessions[session].liquidity_score for session in active_sessions)
        return min(total_liquidity, 1.0)
    
    def get_volatility_multiplier(self, dt: datetime.datetime) -> float:
        active_sessions = self.get_active_sessions(dt)
        
        if not active_sessions:
            return 0.5
        
        if self.is_london_ny_overlap(dt):
            return 1.3
        
        max_volatility = max(self.sessions[session].volatility_multiplier for session in active_sessions)
        return max_volatility
    
    def get_active_currency_pairs(self, dt: datetime.datetime) -> Set[str]:
        active_sessions = self.get_active_sessions(dt)
        
        active_pairs = set()
        for session in active_sessions:
            active_pairs.update(self.sessions[session].major_pairs)
        
        return active_pairs
    
    def is_holiday(self, dt: datetime.datetime) -> Dict[str, bool]:
        date_str = dt.strftime('%Y-%m-%d')
        
        return {
            'UK': date_str in self.holidays['UK'],
            'US': date_str in self.holidays['US'],
            'JP': date_str in self.holidays['JP']
        }
    
    def get_holiday_adjusted_liquidity(self, dt: datetime.datetime) -> float:
        base_liquidity = self.get_liquidity_score(dt)
        holiday_status = self.is_holiday(dt)
        
        adjustment_factor = 1.0
        
        if holiday_status['UK'] and holiday_status['US']:
            adjustment_factor = 0.3
        elif holiday_status['UK'] or holiday_status['US']:
            adjustment_factor = 0.6
        elif holiday_status['JP']:
            adjustment_factor = 0.8
        
        return base_liquidity * adjustment_factor
    
    def get_session_info(self, dt: datetime.datetime) -> Dict:
        active_sessions = self.get_active_sessions(dt)
        overlaps = self.get_session_overlaps(dt)
        
        return {
            'timestamp': dt,
            'active_sessions': [session.value for session in active_sessions],
            'session_overlaps': [(s1.value, s2.value) for s1, s2 in overlaps],
            'is_london_ny_overlap': self.is_london_ny_overlap(dt),
            'liquidity_score': self.get_liquidity_score(dt),
            'volatility_multiplier': self.get_volatility_multiplier(dt),
            'active_currency_pairs': list(self.get_active_currency_pairs(dt)),
            'holiday_status': self.is_holiday(dt),
            'holiday_adjusted_liquidity': self.get_holiday_adjusted_liquidity(dt),
            'session_phase': self._get_session_phase(dt)
        }
    
    def _get_session_phase(self, dt: datetime.datetime) -> str:
        gmt_time = dt.astimezone(pytz.UTC)
        gmt_hour = gmt_time.hour
        
        if 21 <= gmt_hour or gmt_hour < 6:
            return "Asian_Early"
        elif 6 <= gmt_hour < 8:
            return "Asian_Late"
        elif 8 <= gmt_hour < 13:
            return "European_Only"
        elif 13 <= gmt_hour < 17:
            return "European_American_Overlap"
        elif 17 <= gmt_hour < 22:
            return "American_Only"
        else:
            return "Market_Close"
    
    def get_position_size_multiplier(self, dt: datetime.datetime) -> float:
        liquidity = self.get_holiday_adjusted_liquidity(dt)
        volatility = self.get_volatility_multiplier(dt)
        
        if liquidity < 0.3:
            return 0.5
        elif liquidity > 0.8 and volatility > 1.0:
            return 1.2
        else:
            return 1.0
    
    def should_avoid_trading(self, dt: datetime.datetime) -> bool:
        holiday_status = self.is_holiday(dt)
        liquidity = self.get_holiday_adjusted_liquidity(dt)
        
        if holiday_status['UK'] and holiday_status['US']:
            return True
        
        if liquidity < 0.2:
            return True
        
        gmt_time = dt.astimezone(pytz.UTC)
        gmt_hour = gmt_time.hour
        
        if 22 <= gmt_hour or gmt_hour < 1:
            return True
        
        return False