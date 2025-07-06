import unittest
import datetime
import pytz
from src.gym_trading_env.utils.session_manager import SessionManager, MarketSession


class TestSessionManager(unittest.TestCase):
    
    def setUp(self):
        self.session_manager = SessionManager()
    
    def test_london_ny_overlap_detection(self):
        dt_overlap = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        dt_no_overlap = datetime.datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.UTC)
        
        self.assertTrue(self.session_manager.is_london_ny_overlap(dt_overlap))
        self.assertFalse(self.session_manager.is_london_ny_overlap(dt_no_overlap))
    
    def test_session_detection_london_hours(self):
        dt_london = datetime.datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
        active_sessions = self.session_manager.get_active_sessions(dt_london)
        
        self.assertIn(MarketSession.LONDON, active_sessions)
    
    def test_session_detection_tokyo_hours(self):
        dt_tokyo = datetime.datetime(2024, 1, 15, 3, 0, 0, tzinfo=pytz.UTC)
        active_sessions = self.session_manager.get_active_sessions(dt_tokyo)
        
        self.assertIn(MarketSession.TOKYO, active_sessions)
    
    def test_session_detection_ny_hours(self):
        dt_ny = datetime.datetime(2024, 1, 15, 18, 0, 0, tzinfo=pytz.UTC)
        active_sessions = self.session_manager.get_active_sessions(dt_ny)
        
        self.assertIn(MarketSession.NEW_YORK, active_sessions)
    
    def test_liquidity_score_london_ny_overlap(self):
        dt_overlap = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        liquidity = self.session_manager.get_liquidity_score(dt_overlap)
        
        self.assertEqual(liquidity, 1.0)
    
    def test_liquidity_score_single_session(self):
        dt_london_only = datetime.datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.UTC)
        liquidity = self.session_manager.get_liquidity_score(dt_london_only)
        
        self.assertEqual(liquidity, 0.8)
    
    def test_volatility_multiplier_london_ny_overlap(self):
        dt_overlap = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        volatility = self.session_manager.get_volatility_multiplier(dt_overlap)
        
        self.assertEqual(volatility, 1.3)
    
    def test_volatility_multiplier_single_session(self):
        dt_london_only = datetime.datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.UTC)
        volatility = self.session_manager.get_volatility_multiplier(dt_london_only)
        
        self.assertEqual(volatility, 1.2)
    
    def test_active_currency_pairs_london_ny_overlap(self):
        dt_overlap = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        pairs = self.session_manager.get_active_currency_pairs(dt_overlap)
        
        expected_pairs = {"EUR/USD", "GBP/USD", "USD/CHF", "EUR/GBP", "EUR/CHF", "GBP/CHF", "USD/CAD", "USD/JPY"}
        self.assertTrue(expected_pairs.issubset(pairs))
    
    def test_holiday_detection_uk(self):
        dt_uk_holiday = datetime.datetime(2024, 12, 25, 12, 0, 0, tzinfo=pytz.UTC)
        holiday_status = self.session_manager.is_holiday(dt_uk_holiday)
        
        self.assertTrue(holiday_status['UK'])
    
    def test_holiday_detection_us(self):
        dt_us_holiday = datetime.datetime(2024, 7, 4, 12, 0, 0, tzinfo=pytz.UTC)
        holiday_status = self.session_manager.is_holiday(dt_us_holiday)
        
        self.assertTrue(holiday_status['US'])
    
    def test_holiday_detection_japan(self):
        dt_jp_holiday = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        holiday_status = self.session_manager.is_holiday(dt_jp_holiday)
        
        self.assertTrue(holiday_status['JP'])
    
    def test_holiday_adjusted_liquidity_both_holidays(self):
        dt_both_holidays = datetime.datetime(2024, 1, 1, 15, 0, 0, tzinfo=pytz.UTC)
        adjusted_liquidity = self.session_manager.get_holiday_adjusted_liquidity(dt_both_holidays)
        
        self.assertLess(adjusted_liquidity, 0.5)
    
    def test_session_phase_detection(self):
        dt_overlap = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        session_info = self.session_manager.get_session_info(dt_overlap)
        
        self.assertEqual(session_info['session_phase'], "European_American_Overlap")
    
    def test_position_size_multiplier_high_liquidity(self):
        dt_overlap = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        multiplier = self.session_manager.get_position_size_multiplier(dt_overlap)
        
        self.assertEqual(multiplier, 1.2)
    
    def test_position_size_multiplier_low_liquidity(self):
        dt_low_liquidity = datetime.datetime(2024, 1, 1, 15, 0, 0, tzinfo=pytz.UTC)
        multiplier = self.session_manager.get_position_size_multiplier(dt_low_liquidity)
        
        self.assertEqual(multiplier, 0.5)
    
    def test_should_avoid_trading_both_holidays(self):
        dt_both_holidays = datetime.datetime(2024, 1, 1, 15, 0, 0, tzinfo=pytz.UTC)
        should_avoid = self.session_manager.should_avoid_trading(dt_both_holidays)
        
        self.assertTrue(should_avoid)
    
    def test_should_avoid_trading_late_night(self):
        dt_late_night = datetime.datetime(2024, 1, 15, 23, 0, 0, tzinfo=pytz.UTC)
        should_avoid = self.session_manager.should_avoid_trading(dt_late_night)
        
        self.assertTrue(should_avoid)
    
    def test_should_not_avoid_trading_normal_hours(self):
        dt_normal = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        should_avoid = self.session_manager.should_avoid_trading(dt_normal)
        
        self.assertFalse(should_avoid)
    
    def test_session_overlap_detection(self):
        dt_overlap = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        overlaps = self.session_manager.get_session_overlaps(dt_overlap)
        
        self.assertTrue(len(overlaps) > 0)
        self.assertIn((MarketSession.LONDON, MarketSession.NEW_YORK), overlaps)
    
    def test_session_info_completeness(self):
        dt_test = datetime.datetime(2024, 1, 15, 15, 0, 0, tzinfo=pytz.UTC)
        info = self.session_manager.get_session_info(dt_test)
        
        required_keys = [
            'timestamp', 'active_sessions', 'session_overlaps', 'is_london_ny_overlap',
            'liquidity_score', 'volatility_multiplier', 'active_currency_pairs',
            'holiday_status', 'holiday_adjusted_liquidity', 'session_phase'
        ]
        
        for key in required_keys:
            self.assertIn(key, info)
    
    def test_weekend_session_detection(self):
        dt_weekend = datetime.datetime(2024, 1, 13, 15, 0, 0, tzinfo=pytz.UTC)
        active_sessions = self.session_manager.get_active_sessions(dt_weekend)
        
        self.assertGreaterEqual(len(active_sessions), 0)


if __name__ == '__main__':
    unittest.main()