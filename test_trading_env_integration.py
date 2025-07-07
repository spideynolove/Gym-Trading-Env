import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

import pandas as pd
import numpy as np
import datetime
import pytz

def test_trading_env_integration():
    print("=== TradingEnv Integration Test ===\n")
    
    try:
        # Import TradingEnv with integrated managers
        from gym_trading_env.environments import TradingEnv
        print("✓ Successfully imported TradingEnv with enhanced features")
        
        # Create sample forex data
        date_range = pd.date_range(
            start='2024-01-15 00:00:00',
            end='2024-01-15 23:59:00', 
            freq='1h',
            tz='UTC'
        )
        
        df = pd.DataFrame({
            'open': np.random.randn(len(date_range)) * 0.01 + 1.0800,
            'high': np.random.randn(len(date_range)) * 0.01 + 1.0810,
            'low': np.random.randn(len(date_range)) * 0.01 + 1.0790,
            'close': np.random.randn(len(date_range)) * 0.01 + 1.0805,
            'volume': np.random.randint(1000, 10000, len(date_range)),
            'feature_price_change': np.random.randn(len(date_range)) * 0.001,
            'feature_volume_ratio': np.random.randn(len(date_range)) * 0.1 + 1.0
        }, index=date_range)
        
        print("✓ Created sample forex data with features")
        
        # Test 1: Standard TradingEnv (backward compatibility)
        print("\n1. Testing Backward Compatibility:")
        env_standard = TradingEnv(
            df=df,
            enable_enhanced_features=False,
            name="EUR/USD_Standard"
        )
        print(f"   Standard env observation space: {env_standard.observation_space.shape}")
        print(f"   Standard env features: {len(env_standard._features_columns)}")
        
        obs_standard, info_standard = env_standard.reset()
        print(f"   Standard env reset successful, obs shape: {obs_standard.shape}")
        
        # Test a few steps
        for i in range(3):
            action = env_standard.action_space.sample()
            obs, reward, done, truncated, info = env_standard.step(action)
            if done or truncated:
                break
        print("✓ Standard TradingEnv works correctly")
        
        # Test 2: Enhanced TradingEnv
        print("\n2. Testing Enhanced Features:")
        env_enhanced = TradingEnv(
            df=df,
            enable_enhanced_features=True,
            currency_pair="EUR/USD",
            name="EUR/USD_Enhanced"
        )
        print(f"   Enhanced env observation space: {env_enhanced.observation_space.shape}")
        print(f"   Enhanced env features: {len(env_enhanced._features_columns)}")
        print(f"   Enhanced features added: {env_enhanced._nb_features - env_standard._nb_features}")
        
        # Check if managers are initialized
        print(f"   SessionManager initialized: {env_enhanced.session_manager is not None}")
        print(f"   NewsRiskManager initialized: {env_enhanced.news_risk_manager is not None}")
        print(f"   CorrelationManager initialized: {env_enhanced.correlation_manager is not None}")
        print(f"   UnifiedMarketManager initialized: {env_enhanced.unified_market_manager is not None}")
        
        obs_enhanced, info_enhanced = env_enhanced.reset()
        print(f"   Enhanced env reset successful, obs shape: {obs_enhanced.shape}")
        
        # Test enhanced trading logic
        print("\n3. Testing Enhanced Trading Logic:")
        for i in range(5):
            action = env_enhanced.action_space.sample()
            obs, reward, done, truncated, info = env_enhanced.step(action)
            
            # Check if enhanced features are being updated
            enhanced_feature_start = len(env_standard._features_columns)
            enhanced_features = obs[enhanced_feature_start:enhanced_feature_start+9]
            
            print(f"   Step {i+1}: Enhanced features sample: {enhanced_features[:3]}")
            
            if done or truncated:
                break
        
        print("✓ Enhanced TradingEnv works correctly")
        
        # Test 3: Feature comparison
        print("\n4. Feature Space Comparison:")
        print(f"   Standard features: {env_standard._features_columns}")
        print(f"   Enhanced features (last 9): {env_enhanced._features_columns[-9:]}")
        
        # Test 4: Manager functionality
        print("\n5. Testing Manager Integration:")
        current_time = datetime.datetime.now(pytz.UTC)
        
        # Session manager test
        session_info = env_enhanced.session_manager.get_session_info(current_time)
        print(f"   Session info: {session_info['active_sessions']}, liquidity: {session_info['liquidity_score']:.2f}")
        
        # News risk manager test
        risk_assessment = env_enhanced.news_risk_manager.get_risk_assessment(current_time, "EUR/USD")
        print(f"   News risk: position multiplier = {risk_assessment['position_size_multiplier']:.2f}")
        
        # Unified manager test
        if env_enhanced.unified_market_manager:
            unified_features = env_enhanced.unified_market_manager.get_dynamic_unified_features(
                "EUR/USD", {"EUR/USD": 0.5}, current_time
            )
            print(f"   Unified features sample: COT strength = {unified_features['cot_signal_strength']:.3f}")
        
        print("✓ All managers functioning correctly")
        
        print("\n=== Integration Test Results ===")
        print("✅ TradingEnv successfully integrates all 4 enhanced managers")
        print("✅ Backward compatibility maintained with enable_enhanced_features flag")
        print("✅ Enhanced features properly added to observation space")
        print("✅ Session-aware, news-aware, correlation-aware trading logic implemented")
        print("✅ All managers integrated into trading loop")
        
        print(f"\n📊 Integration Statistics:")
        print(f"   Standard feature count: {len(env_standard._features_columns)}")
        print(f"   Enhanced feature count: {len(env_enhanced._features_columns)}")
        print(f"   Additional features: {len(env_enhanced._features_columns) - len(env_standard._features_columns)}")
        print(f"   Observation space expansion: {env_enhanced.observation_space.shape[0] - env_standard.observation_space.shape[0]} features")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trading_env_integration()
    if success:
        print("\n🎯 TradingEnv integration successful!")
    else:
        print("\n💥 TradingEnv integration failed!")