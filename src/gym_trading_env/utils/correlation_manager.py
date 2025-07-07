import datetime
import pytz
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import math


class CorrelationRegime(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    EXTREME = "Extreme"


@dataclass
class CorrelationData:
    pair1: str
    pair2: str
    correlation: float
    window_days: int
    timestamp: datetime.datetime
    regime: CorrelationRegime
    z_score: float = 0.0
    
    def is_high_correlation(self) -> bool:
        return abs(self.correlation) > 0.7
    
    def is_extreme_correlation(self) -> bool:
        return abs(self.correlation) > 0.9


class CurrencyStrengthIndex:
    def __init__(self):
        self.currency_weights = {
            'USD': 0.25,
            'EUR': 0.20,
            'GBP': 0.15,
            'JPY': 0.12,
            'CHF': 0.08,
            'CAD': 0.08,
            'AUD': 0.07,
            'NZD': 0.05
        }
    
    def calculate_strength(self, currency: str, price_changes: Dict[str, float]) -> float:
        strength = 0.0
        weight_sum = 0.0
        
        for pair, change in price_changes.items():
            if currency in pair:
                pair_clean = pair.replace('/', '').replace('_', '')
                base_currency = pair_clean[:3]
                quote_currency = pair_clean[3:]
                
                if base_currency == currency:
                    strength += change * self.currency_weights.get(quote_currency, 0.05)
                    weight_sum += self.currency_weights.get(quote_currency, 0.05)
                elif quote_currency == currency:
                    strength -= change * self.currency_weights.get(base_currency, 0.05)
                    weight_sum += self.currency_weights.get(base_currency, 0.05)
        
        return strength / weight_sum if weight_sum > 0 else 0.0


class CorrelationManager:
    
    def __init__(self):
        self.correlation_windows = [30, 60, 90]
        self.correlation_history: Dict[Tuple[str, str, int], List[CorrelationData]] = {}
        self.price_history: Dict[str, List[Tuple[datetime.datetime, float]]] = {}
        self.currency_strength = CurrencyStrengthIndex()
        
        self.correlation_thresholds = {
            CorrelationRegime.LOW: (0.0, 0.3),
            CorrelationRegime.MEDIUM: (0.3, 0.7),
            CorrelationRegime.HIGH: (0.7, 0.9),
            CorrelationRegime.EXTREME: (0.9, 1.0)
        }
        
        self.major_pairs = [
            'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF',
            'AUD/USD', 'USD/CAD', 'NZD/USD'
        ]
        
        self.cross_pairs = [
            'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/AUD',
            'GBP/JPY', 'GBP/CHF', 'GBP/AUD',
            'AUD/JPY', 'AUD/CAD', 'NZD/JPY'
        ]
        
        self.all_pairs = self.major_pairs + self.cross_pairs
        
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        base_date = datetime.datetime(2024, 1, 1, tzinfo=pytz.UTC)
        
        # Generate sample price data for correlation calculation
        import random
        random.seed(42)  # For reproducible results
        
        for pair in self.major_pairs:
            prices = []
            base_price = 1.0 if 'USD' in pair[:3] else 0.8
            
            for i in range(100):  # 100 days of data
                date = base_date + datetime.timedelta(days=i)
                
                # Create correlated movements for EUR/USD and GBP/USD
                if pair == 'EUR/USD':
                    price_change = random.gauss(0, 0.01)
                    self._eur_usd_change = price_change  # Store for GBP/USD correlation
                elif pair == 'GBP/USD':
                    # High correlation with EUR/USD
                    correlated_change = getattr(self, '_eur_usd_change', 0) * 0.8
                    independent_change = random.gauss(0, 0.005)
                    price_change = correlated_change + independent_change
                else:
                    price_change = random.gauss(0, 0.008)
                
                base_price += price_change
                prices.append((date, base_price))
            
            self.price_history[pair] = prices
    
    def add_price_data(self, currency_pair: str, timestamp: datetime.datetime, price: float):
        if currency_pair not in self.price_history:
            self.price_history[currency_pair] = []
        
        self.price_history[currency_pair].append((timestamp, price))
        
        # Keep only last 200 data points for memory efficiency
        if len(self.price_history[currency_pair]) > 200:
            self.price_history[currency_pair] = self.price_history[currency_pair][-200:]
    
    def calculate_returns(self, currency_pair: str, window_days: int) -> List[float]:
        if currency_pair not in self.price_history:
            return []
        
        prices = self.price_history[currency_pair]
        if len(prices) < window_days + 1:
            return []
        
        recent_prices = prices[-window_days-1:]
        returns = []
        
        for i in range(1, len(recent_prices)):
            prev_price = recent_prices[i-1][1]
            curr_price = recent_prices[i][1]
            
            if prev_price > 0:
                return_val = (curr_price - prev_price) / prev_price
                returns.append(return_val)
        
        return returns
    
    def calculate_correlation(self, pair1: str, pair2: str, window_days: int) -> Optional[float]:
        returns1 = self.calculate_returns(pair1, window_days)
        returns2 = self.calculate_returns(pair2, window_days)
        
        if len(returns1) < window_days or len(returns2) < window_days:
            return None
        
        # Ensure same length
        min_length = min(len(returns1), len(returns2))
        returns1 = returns1[-min_length:]
        returns2 = returns2[-min_length:]
        
        if min_length < 10:  # Need minimum data points
            return None
        
        # Calculate Pearson correlation
        mean1 = sum(returns1) / len(returns1)
        mean2 = sum(returns2) / len(returns2)
        
        numerator = sum((x - mean1) * (y - mean2) for x, y in zip(returns1, returns2))
        
        sum_sq1 = sum((x - mean1) ** 2 for x in returns1)
        sum_sq2 = sum((y - mean2) ** 2 for y in returns2)
        
        denominator = math.sqrt(sum_sq1 * sum_sq2)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def classify_correlation_regime(self, correlation: float) -> CorrelationRegime:
        abs_corr = abs(correlation)
        
        for regime, (low, high) in self.correlation_thresholds.items():
            if low <= abs_corr < high:
                return regime
        
        return CorrelationRegime.EXTREME
    
    def calculate_correlation_z_score(self, pair1: str, pair2: str, window_days: int) -> float:
        key = (pair1, pair2, window_days)
        
        if key not in self.correlation_history:
            return 0.0
        
        history = self.correlation_history[key]
        if len(history) < 20:  # Need sufficient history
            return 0.0
        
        correlations = [data.correlation for data in history[-20:]]
        mean_corr = sum(correlations) / len(correlations)
        
        variance = sum((c - mean_corr) ** 2 for c in correlations) / len(correlations)
        std_dev = math.sqrt(variance) if variance > 0 else 1.0
        
        current_corr = correlations[-1]
        return (current_corr - mean_corr) / std_dev
    
    def update_correlations(self, timestamp: datetime.datetime):
        for pair1 in self.all_pairs:
            for pair2 in self.all_pairs:
                if pair1 >= pair2:  # Avoid duplicate calculations
                    continue
                
                for window in self.correlation_windows:
                    correlation = self.calculate_correlation(pair1, pair2, window)
                    
                    if correlation is not None:
                        regime = self.classify_correlation_regime(correlation)
                        z_score = self.calculate_correlation_z_score(pair1, pair2, window)
                        
                        corr_data = CorrelationData(
                            pair1=pair1,
                            pair2=pair2,
                            correlation=correlation,
                            window_days=window,
                            timestamp=timestamp,
                            regime=regime,
                            z_score=z_score
                        )
                        
                        key = (pair1, pair2, window)
                        if key not in self.correlation_history:
                            self.correlation_history[key] = []
                        
                        self.correlation_history[key].append(corr_data)
                        
                        # Keep only last 100 correlation data points
                        if len(self.correlation_history[key]) > 100:
                            self.correlation_history[key] = self.correlation_history[key][-100:]
    
    def get_correlation(self, pair1: str, pair2: str, window_days: int = 30) -> Optional[CorrelationData]:
        # Ensure consistent ordering
        if pair1 > pair2:
            pair1, pair2 = pair2, pair1
        
        key = (pair1, pair2, window_days)
        
        if key in self.correlation_history and self.correlation_history[key]:
            return self.correlation_history[key][-1]
        
        return None
    
    def get_highly_correlated_pairs(self, reference_pair: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        highly_correlated = []
        
        for pair in self.all_pairs:
            if pair == reference_pair:
                continue
            
            corr_data = self.get_correlation(reference_pair, pair)
            if corr_data and abs(corr_data.correlation) >= threshold:
                highly_correlated.append((pair, corr_data.correlation))
        
        return sorted(highly_correlated, key=lambda x: abs(x[1]), reverse=True)
    
    def calculate_portfolio_correlation_risk(self, positions: Dict[str, float]) -> float:
        total_risk = 0.0
        position_pairs = list(positions.keys())
        
        for i, pair1 in enumerate(position_pairs):
            for pair2 in position_pairs[i+1:]:
                corr_data = self.get_correlation(pair1, pair2)
                if corr_data:
                    correlation = corr_data.correlation
                    position1 = abs(positions[pair1])
                    position2 = abs(positions[pair2])
                    
                    # Calculate correlation-weighted risk
                    correlation_risk = correlation * position1 * position2
                    total_risk += abs(correlation_risk)
        
        return total_risk
    
    def get_correlation_adjusted_position_size(self, currency_pair: str, base_position: float, 
                                             existing_positions: Dict[str, float]) -> float:
        correlation_exposure = 0.0
        
        for existing_pair, existing_size in existing_positions.items():
            if existing_pair == currency_pair:
                continue
            
            corr_data = self.get_correlation(currency_pair, existing_pair)
            if corr_data:
                # Calculate directional correlation exposure
                correlation = corr_data.correlation
                
                # Check if positions are in same direction
                if base_position * existing_size > 0:  # Same direction
                    correlation_exposure += abs(correlation) * abs(existing_size)
                else:  # Opposite direction
                    correlation_exposure -= abs(correlation) * abs(existing_size)
        
        # Reduce position size based on correlation exposure
        if correlation_exposure > 0.5:  # High correlation exposure
            adjustment_factor = 1.0 / (1.0 + correlation_exposure)
            return base_position * adjustment_factor
        
        return base_position
    
    def detect_correlation_regime_change(self, pair1: str, pair2: str, window_days: int = 30) -> bool:
        key = (min(pair1, pair2), max(pair1, pair2), window_days)
        
        if key not in self.correlation_history:
            return False
        
        history = self.correlation_history[key]
        if len(history) < 2:
            return False
        
        current_regime = history[-1].regime
        previous_regime = history[-2].regime
        
        return current_regime != previous_regime
    
    def get_currency_strength_index(self, currency: str, timestamp: datetime.datetime) -> float:
        price_changes = {}
        
        for pair in self.all_pairs:
            if currency in pair:
                returns = self.calculate_returns(pair, 5)  # 5-day strength
                if returns:
                    avg_return = sum(returns) / len(returns)
                    price_changes[pair] = avg_return
        
        return self.currency_strength.calculate_strength(currency, price_changes)
    
    def get_portfolio_diversification_score(self, positions: Dict[str, float]) -> float:
        if len(positions) <= 1:
            return 1.0  # Perfect diversification with single position
        
        total_correlation = 0.0
        pair_count = 0
        
        position_pairs = list(positions.keys())
        for i, pair1 in enumerate(position_pairs):
            for pair2 in position_pairs[i+1:]:
                corr_data = self.get_correlation(pair1, pair2)
                if corr_data:
                    total_correlation += abs(corr_data.correlation)
                    pair_count += 1
        
        if pair_count == 0:
            return 1.0
        
        avg_correlation = total_correlation / pair_count
        diversification_score = 1.0 - avg_correlation
        
        return max(0.0, min(1.0, diversification_score))
    
    def get_correlation_matrix(self, pairs: List[str], window_days: int = 30) -> Dict[Tuple[str, str], float]:
        matrix = {}
        
        for pair1 in pairs:
            for pair2 in pairs:
                if pair1 == pair2:
                    matrix[(pair1, pair2)] = 1.0
                else:
                    corr_data = self.get_correlation(pair1, pair2, window_days)
                    correlation = corr_data.correlation if corr_data else 0.0
                    matrix[(pair1, pair2)] = correlation
        
        return matrix
    
    def get_correlation_analysis(self, currency_pair: str, existing_positions: Dict[str, float]) -> Dict:
        highly_corr = self.get_highly_correlated_pairs(currency_pair, threshold=0.5)
        portfolio_risk = self.calculate_portfolio_correlation_risk(existing_positions)
        diversification = self.get_portfolio_diversification_score(existing_positions)
        
        # Extract base currency for strength analysis
        pair_clean = currency_pair.replace('/', '').replace('_', '')
        base_currency = pair_clean[:3]
        quote_currency = pair_clean[3:]
        
        base_strength = self.get_currency_strength_index(base_currency, datetime.datetime.now(pytz.UTC))
        quote_strength = self.get_currency_strength_index(quote_currency, datetime.datetime.now(pytz.UTC))
        
        return {
            'currency_pair': currency_pair,
            'highly_correlated_pairs': highly_corr,
            'portfolio_correlation_risk': portfolio_risk,
            'diversification_score': diversification,
            'base_currency_strength': base_strength,
            'quote_currency_strength': quote_strength,
            'net_currency_strength': base_strength - quote_strength,
            'correlation_warnings': self._get_correlation_warnings(currency_pair, existing_positions)
        }
    
    def _get_correlation_warnings(self, currency_pair: str, existing_positions: Dict[str, float]) -> List[str]:
        warnings = []
        
        for existing_pair, position in existing_positions.items():
            if existing_pair == currency_pair:
                continue
            
            corr_data = self.get_correlation(currency_pair, existing_pair)
            if corr_data and corr_data.is_extreme_correlation():
                warnings.append(f"Extreme correlation ({corr_data.correlation:.2f}) with {existing_pair}")
            elif corr_data and corr_data.is_high_correlation():
                warnings.append(f"High correlation ({corr_data.correlation:.2f}) with {existing_pair}")
        
        portfolio_risk = self.calculate_portfolio_correlation_risk(existing_positions)
        if portfolio_risk > 1.0:
            warnings.append(f"High portfolio correlation risk: {portfolio_risk:.2f}")
        
        return warnings