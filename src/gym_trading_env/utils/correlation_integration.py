import datetime
import pytz
from typing import Dict, Any, Optional, List, Tuple
from .correlation_manager import CorrelationManager


class CorrelationIntegration:
    
    def __init__(self, correlation_manager: Optional[CorrelationManager] = None):
        self.correlation_manager = correlation_manager or CorrelationManager()
    
    def add_price_update(self, currency_pair: str, timestamp, price: float):
        if isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        self.correlation_manager.add_price_data(currency_pair, dt, price)
        
        # Update correlations every 24 hours or when enough new data
        if len(self.correlation_manager.price_history.get(currency_pair, [])) % 24 == 0:
            self.correlation_manager.update_correlations(dt)
    
    def get_correlation_adjusted_position_size(self, currency_pair: str, base_position: float, 
                                             existing_positions: Dict[str, float]) -> float:
        return self.correlation_manager.get_correlation_adjusted_position_size(
            currency_pair, base_position, existing_positions
        )
    
    def get_portfolio_risk_score(self, positions: Dict[str, float]) -> float:
        correlation_risk = self.correlation_manager.calculate_portfolio_correlation_risk(positions)
        diversification = self.correlation_manager.get_portfolio_diversification_score(positions)
        
        # Combine correlation risk and diversification into single score
        # Higher score = higher risk
        risk_score = correlation_risk * (1 - diversification)
        return min(1.0, max(0.0, risk_score))
    
    def should_reduce_position_due_to_correlation(self, currency_pair: str, 
                                                existing_positions: Dict[str, float],
                                                correlation_threshold: float = 0.8) -> bool:
        highly_correlated = self.correlation_manager.get_highly_correlated_pairs(
            currency_pair, threshold=correlation_threshold
        )
        
        for corr_pair, correlation in highly_correlated:
            if corr_pair in existing_positions and abs(existing_positions[corr_pair]) > 0.1:
                return True
        
        return False
    
    def get_correlation_warnings(self, currency_pair: str, existing_positions: Dict[str, float]) -> List[str]:
        analysis = self.correlation_manager.get_correlation_analysis(currency_pair, existing_positions)
        return analysis['correlation_warnings']
    
    def get_currency_strength_signals(self, currency_pair: str) -> Dict[str, float]:
        pair_clean = currency_pair.replace('/', '').replace('_', '')
        base_currency = pair_clean[:3]
        quote_currency = pair_clean[3:]
        
        current_time = datetime.datetime.now(pytz.UTC)
        
        base_strength = self.correlation_manager.get_currency_strength_index(base_currency, current_time)
        quote_strength = self.correlation_manager.get_currency_strength_index(quote_currency, current_time)
        
        return {
            'base_currency': base_currency,
            'quote_currency': quote_currency,
            'base_strength': base_strength,
            'quote_strength': quote_strength,
            'net_strength': base_strength - quote_strength,
            'strength_signal': 1.0 if base_strength > quote_strength else -1.0
        }
    
    def get_dynamic_correlation_features(self, currency_pair: str, existing_positions: Dict[str, float]) -> Dict[str, float]:
        analysis = self.correlation_manager.get_correlation_analysis(currency_pair, existing_positions)
        strength_signals = self.get_currency_strength_signals(currency_pair)
        
        # Get correlation with EUR/USD as benchmark
        eur_usd_corr = self.correlation_manager.get_correlation(currency_pair, "EUR/USD")
        eur_usd_correlation = eur_usd_corr.correlation if eur_usd_corr else 0.0
        
        # Get correlation with GBP/USD
        gbp_usd_corr = self.correlation_manager.get_correlation(currency_pair, "GBP/USD")
        gbp_usd_correlation = gbp_usd_corr.correlation if gbp_usd_corr else 0.0
        
        return {
            'portfolio_correlation_risk': analysis['portfolio_correlation_risk'],
            'diversification_score': analysis['diversification_score'],
            'base_currency_strength': strength_signals['base_strength'],
            'quote_currency_strength': strength_signals['quote_strength'],
            'net_currency_strength': strength_signals['net_strength'],
            'eur_usd_correlation': abs(eur_usd_correlation),
            'gbp_usd_correlation': abs(gbp_usd_correlation),
            'max_pair_correlation': self._get_max_correlation_with_existing(currency_pair, existing_positions),
            'correlation_regime_high': 1.0 if self._is_high_correlation_regime(currency_pair) else 0.0,
            'position_reduction_factor': self._get_position_reduction_factor(currency_pair, existing_positions)
        }
    
    def _get_max_correlation_with_existing(self, currency_pair: str, existing_positions: Dict[str, float]) -> float:
        max_correlation = 0.0
        
        for existing_pair in existing_positions.keys():
            if existing_pair == currency_pair:
                continue
            
            corr_data = self.correlation_manager.get_correlation(currency_pair, existing_pair)
            if corr_data:
                max_correlation = max(max_correlation, abs(corr_data.correlation))
        
        return max_correlation
    
    def _is_high_correlation_regime(self, currency_pair: str) -> bool:
        # Check if any major correlation is in high regime
        major_pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY']
        
        for pair in major_pairs:
            if pair == currency_pair:
                continue
            
            corr_data = self.correlation_manager.get_correlation(currency_pair, pair)
            if corr_data and corr_data.regime.value in ['High', 'Extreme']:
                return True
        
        return False
    
    def _get_position_reduction_factor(self, currency_pair: str, existing_positions: Dict[str, float]) -> float:
        base_position = 1.0
        adjusted_position = self.correlation_manager.get_correlation_adjusted_position_size(
            currency_pair, base_position, existing_positions
        )
        return adjusted_position / base_position
    
    def add_correlation_features_to_dataframe(self, df, currency_pair: str, 
                                            existing_positions: Dict[str, float] = None,
                                            timestamp_column: str = None):
        if existing_positions is None:
            existing_positions = {}
        
        if timestamp_column is None:
            timestamps = df.index
        else:
            timestamps = df[timestamp_column]
        
        correlation_features = {}
        
        for i, timestamp in enumerate(timestamps):
            # Update price data for correlation calculation
            if 'close' in df.columns:
                close_price = df.iloc[i]['close']
                self.add_price_update(currency_pair, timestamp, close_price)
            
            features = self.get_dynamic_correlation_features(currency_pair, existing_positions)
            
            for feature_name, value in features.items():
                if f'feature_correlation_{feature_name}' not in correlation_features:
                    correlation_features[f'feature_correlation_{feature_name}'] = []
                correlation_features[f'feature_correlation_{feature_name}'].append(value)
        
        for feature_name, values in correlation_features.items():
            df[feature_name] = values
        
        return df
    
    def get_correlation_context(self, currency_pair: str, existing_positions: Dict[str, float]) -> Dict[str, Any]:
        return self.correlation_manager.get_correlation_analysis(currency_pair, existing_positions)
    
    def force_update_correlations(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.datetime.now(pytz.UTC)
        elif isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=pytz.UTC)
        
        self.correlation_manager.update_correlations(timestamp)
    
    def get_correlation_matrix(self, pairs: List[str], window_days: int = 30) -> Dict[Tuple[str, str], float]:
        return self.correlation_manager.get_correlation_matrix(pairs, window_days)


def dynamic_feature_correlation_portfolio_risk(history):
    integration = CorrelationIntegration()
    
    # Assume current positions from history
    existing_positions = {"EUR/USD": 0.5}  # Should be parameterized
    currency_pair = "GBP/USD"  # Should be parameterized
    
    features = integration.get_dynamic_correlation_features(currency_pair, existing_positions)
    return features['portfolio_correlation_risk']


def dynamic_feature_correlation_diversification(history):
    integration = CorrelationIntegration()
    
    existing_positions = {"EUR/USD": 0.5}
    currency_pair = "GBP/USD"
    
    features = integration.get_dynamic_correlation_features(currency_pair, existing_positions)
    return features['diversification_score']


def dynamic_feature_correlation_base_strength(history):
    integration = CorrelationIntegration()
    
    existing_positions = {}
    currency_pair = "EUR/USD"
    
    features = integration.get_dynamic_correlation_features(currency_pair, existing_positions)
    return features['base_currency_strength']


def dynamic_feature_correlation_max_correlation(history):
    integration = CorrelationIntegration()
    
    existing_positions = {"EUR/USD": 0.5}
    currency_pair = "GBP/USD"
    
    features = integration.get_dynamic_correlation_features(currency_pair, existing_positions)
    return features['max_pair_correlation']


def dynamic_feature_correlation_position_reduction(history):
    integration = CorrelationIntegration()
    
    existing_positions = {"EUR/USD": 0.5}
    currency_pair = "GBP/USD"
    
    features = integration.get_dynamic_correlation_features(currency_pair, existing_positions)
    return features['position_reduction_factor']