import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Union, Any

class LazyCallable:
    _cache = {}
    
    def __init__(self, name):
        self.n = name
        self.f = LazyCallable._cache.get(name)
    
    def __call__(self, *a, **k):
        if self.f is None:
            modn, funcn = self.n.rsplit('.', 1)
            if modn not in sys.modules:
                __import__(modn)
            self.f = getattr(sys.modules[modn], funcn)
            LazyCallable._cache[self.n] = self.f
        return self.f(*a, **k)

class TechnicalIndicators:
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame, indicators: Dict[str, Dict]) -> pd.DataFrame:
        df_result = df.copy()
        
        for indicator, params in indicators.items():
            time_periods = params.get('time_periods', [])
            input_columns = params.get('input_columns', [])
            output_columns = params.get('output_columns', [])
            
            if isinstance(input_columns, str):
                input_columns = [input_columns]
            if isinstance(output_columns, str):
                output_columns = [output_columns]
            if not isinstance(time_periods, list) or time_periods == "":
                time_periods = [""]
            
            for time_period in time_periods:
                indicator_func = LazyCallable(f'talib.{indicator}')
                
                if len(output_columns) > 1:
                    column_names = [f'{indicator}{col}{time_period}' for col in output_columns]
                    
                    if time_period:
                        outputs = indicator_func(*[df_result[col] for col in input_columns], timeperiod=time_period)
                    else:
                        outputs = indicator_func(*[df_result[col] for col in input_columns])
                    
                    for col, output in zip(column_names, outputs):
                        df_result[col] = output
                else:
                    column_name = f'{indicator}{time_period}'
                    
                    if time_period:
                        df_result[column_name] = indicator_func(*[df_result[col] for col in input_columns], timeperiod=time_period)
                    else:
                        df_result[column_name] = indicator_func(*[df_result[col] for col in input_columns])
        
        return df_result

class RollingFeatures:
    SUPPORTED_FUNCTIONS = ['mean', 'sum', 'max', 'min', 'var', 'std', 'skew', 'kurt', 'shift', 'diff']
    
    @staticmethod
    def add_rolling_functions(df: pd.DataFrame, column_names: List[str], 
                            window_sizes: List[Union[int, str]], 
                            functions: List[str]) -> pd.DataFrame:
        df_result = df.copy()
        
        for column_name in column_names:
            if column_name not in df_result.columns:
                continue
                
            for window_size in window_sizes:
                for func in functions:
                    if func not in RollingFeatures.SUPPORTED_FUNCTIONS:
                        raise ValueError(f"Unsupported function: {func}")
                    
                    column_suffix = f'{column_name}{func.title()}{window_size}'
                    rolling_obj = df_result[column_name].rolling(window=window_size)
                    
                    if func == 'mean':
                        df_result[column_suffix] = rolling_obj.mean()
                    elif func == 'sum':
                        df_result[column_suffix] = rolling_obj.sum()
                    elif func == 'max':
                        df_result[column_suffix] = rolling_obj.max()
                    elif func == 'min':
                        df_result[column_suffix] = rolling_obj.min()
                    elif func == 'var':
                        df_result[column_suffix] = rolling_obj.var()
                    elif func == 'std':
                        df_result[column_suffix] = rolling_obj.std()
                    elif func == 'skew':
                        df_result[column_suffix] = rolling_obj.skew()
                    elif func == 'kurt':
                        df_result[column_suffix] = rolling_obj.kurt()
                    elif func == 'shift':
                        df_result[column_suffix] = df_result[column_name].shift(window_size)
                    elif func == 'diff':
                        df_result[column_suffix] = df_result[column_name].diff(window_size)
        
        return df_result

class PercentageChanges:
    PERIOD_MAP = {'W': 5, 'M': 21, 'Q': 63, 'Y': 252, '3Y': 756}
    
    @staticmethod
    def add_percentage_change(df: pd.DataFrame, column_name: str, periods: List[Union[str, int]]) -> pd.DataFrame:
        df_result = df.copy()
        
        for period in periods:
            if period == 'YTD':
                first_value = df_result[column_name].iloc[0]
                if first_value != 0:
                    df_result['YTD'] = (df_result[column_name] / first_value - 1) * 100
                else:
                    df_result['YTD'] = 0
            else:
                period_value = PercentageChanges.PERIOD_MAP.get(period, period)
                new_column_name = f'Chg{period}'
                df_result[new_column_name] = df_result[column_name].pct_change(periods=period_value) * 100
        
        return df_result

class PivotPoints:
    STANDARD_FORMULAS = {
        'PP': '(H + L + C) / 3',
        'S1': '(2 * PP) - H',
        'S2': 'PP - (H - L)',
        'S3': 'L - 2 * (H - PP)',
        'R1': '(2 * PP) - L',
        'R2': 'PP + (H - L)',
        'R3': 'H + 2 * (PP - L)'
    }
    
    WOODIE_FORMULAS = {
        'PP': '(H + L + 2 * C) / 4',
        'S1': '(2 * PP) - H',
        'S2': 'PP - (H - L)',
        'R1': '(2 * PP) - L',
        'R2': 'PP + (H - L)'
    }
    
    CAMARILLA_FORMULAS = {
        'PP': '(H + L + C) / 3',
        'S1': 'C - (H - L) * 1.1 / 12',
        'S2': 'C - (H - L) * 1.1 / 6',
        'S3': 'C - (H - L) * 1.1 / 4',
        'S4': 'C - (H - L) * 1.1 / 2',
        'R1': 'C + (H - L) * 1.1 / 12',
        'R2': 'C + (H - L) * 1.1 / 6',
        'R3': 'C + (H - L) * 1.1 / 4',
        'R4': 'C + (H - L) * 1.1 / 2'
    }
    
    @staticmethod
    def calculate_pivot_points(df: pd.DataFrame, suffix: str = '', 
                             pivot_type: str = 'standard') -> pd.DataFrame:
        df_result = df.copy()
        
        if pivot_type == 'standard':
            formulas = PivotPoints.STANDARD_FORMULAS
        elif pivot_type == 'woodie':
            formulas = PivotPoints.WOODIE_FORMULAS
        elif pivot_type == 'camarilla':
            formulas = PivotPoints.CAMARILLA_FORMULAS
        else:
            raise ValueError(f"Unsupported pivot type: {pivot_type}")
        
        high_col = f'High{suffix}' if f'High{suffix}' in df_result.columns else 'high'
        low_col = f'Low{suffix}' if f'Low{suffix}' in df_result.columns else 'low' 
        close_col = f'Close{suffix}' if f'Close{suffix}' in df_result.columns else 'close'
        
        for col, formula in formulas.items():
            formula_expr = formula.replace('H', f'df_result["{high_col}"]')
            formula_expr = formula_expr.replace('L', f'df_result["{low_col}"]')
            formula_expr = formula_expr.replace('C', f'df_result["{close_col}"]')
            formula_expr = formula_expr.replace('PP', 'df_result["PP"]')
            
            df_result[col] = eval(formula_expr)
        
        return df_result
    
    @staticmethod
    def calculate_pivot_location(df: pd.DataFrame, column: str, suffix: str = '',
                               pivot_points: List[str] = ['S3', 'S2', 'S1', 'PP', 'R1', 'R2', 'R3'],
                               choices: List[Any] = None) -> np.ndarray:
        if choices is None:
            choices = list(range(len(pivot_points) + 1))
        
        price_col = column + suffix
        conditions = []
        
        for i in range(len(pivot_points) - 1):
            condition = (df[price_col] > df[pivot_points[i]]) & (df[price_col] < df[pivot_points[i + 1]])
            conditions.append(condition)
        
        conditions.append(df[price_col] > df[pivot_points[-1]])
        conditions.append(df[price_col] < df[pivot_points[0]])
        
        choices_adjusted = choices[:len(conditions)]
        return np.select(conditions, choices_adjusted, default=np.nan)

class FibonacciLevels:
    STANDARD_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
    EXTENDED_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.707, 0.786, 0.886, 1.382, 1.5, 1.618, 1.786, 1.886, 2.0, 2.618, 2.786, 2.886]
    IMPORTANT_LEVELS = [1.786, 1.886, 2.786, 2.886]
    
    @staticmethod
    def calculate_fib_levels(start: float, end: float, levels: List[float]) -> List[float]:
        ratios = sorted([0.0] + levels + [1.0])
        level_prices = [round(start + ratio * (end - start), 6) for ratio in ratios]
        return level_prices[1:-1]
    
    @staticmethod
    def add_fibonacci_levels(df: pd.DataFrame, high_col: str = 'high', low_col: str = 'low',
                           levels: List[float] = None, level_type: str = 'standard') -> pd.DataFrame:
        df_result = df.copy()
        
        if levels is None:
            levels = FibonacciLevels.EXTENDED_LEVELS if level_type == 'extended' else FibonacciLevels.STANDARD_LEVELS
        
        fib_data = df_result.apply(
            lambda row: FibonacciLevels.calculate_fib_levels(row[low_col], row[high_col], levels), 
            axis=1
        )
        
        fib_df = pd.DataFrame(fib_data.tolist(), index=df_result.index)
        level_names = [f'fib_{level}' for level in levels]
        fib_df.columns = level_names
        
        return pd.concat([df_result, fib_df], axis=1)

class PriceTransformations:
    @staticmethod
    def add_basic_transformations(df: pd.DataFrame, 
                                open_col: str = 'open',
                                high_col: str = 'high', 
                                low_col: str = 'low',
                                close_col: str = 'close',
                                volume_col: str = 'volume') -> pd.DataFrame:
        df_result = df.copy()
        
        df_result['ohlc_average'] = (df_result[open_col] + df_result[high_col] + 
                                   df_result[low_col] + df_result[close_col]) / 4
        df_result['hl_average'] = (df_result[high_col] + df_result[low_col]) / 2
        df_result['oc_average'] = (df_result[open_col] + df_result[close_col]) / 2
        
        df_result['hl_range'] = df_result[high_col] - df_result[low_col]
        df_result['oc_range'] = abs(df_result[open_col] - df_result[close_col])
        
        df_result['upper_shadow'] = df_result[high_col] - df_result[[open_col, close_col]].max(axis=1)
        df_result['lower_shadow'] = df_result[[open_col, close_col]].min(axis=1) - df_result[low_col]
        df_result['real_body'] = abs(df_result[close_col] - df_result[open_col])
        
        df_result['typical_price'] = (df_result[high_col] + df_result[low_col] + df_result[close_col]) / 3
        df_result['weighted_close'] = (df_result[high_col] + df_result[low_col] + 2 * df_result[close_col]) / 4
        
        if volume_col in df_result.columns:
            df_result['price_volume'] = df_result[close_col] * df_result[volume_col]
            df_result['vwap_approx'] = (df_result['price_volume'].rolling(20).sum() / 
                                      df_result[volume_col].rolling(20).sum())
        
        for col in [open_col, high_col, low_col, close_col]:
            df_result[f'{col}_change'] = df_result[col].pct_change() * 100
            df_result[f'{col}_change_abs'] = df_result[f'{col}_change'].abs()
        
        return df_result
    
    @staticmethod
    def add_price_patterns(df: pd.DataFrame,
                         open_col: str = 'open', 
                         high_col: str = 'high',
                         low_col: str = 'low', 
                         close_col: str = 'close') -> pd.DataFrame:
        df_result = df.copy()
        
        body_size = abs(df_result[close_col] - df_result[open_col])
        range_size = df_result[high_col] - df_result[low_col]
        upper_shadow = df_result[high_col] - df_result[[open_col, close_col]].max(axis=1)
        lower_shadow = df_result[[open_col, close_col]].min(axis=1) - df_result[low_col]
        
        df_result['doji'] = (body_size / (range_size + 1e-8) < 0.1).astype(int)
        df_result['hammer'] = ((lower_shadow > 2 * body_size) & 
                             (upper_shadow < 0.1 * range_size)).astype(int)
        df_result['shooting_star'] = ((upper_shadow > 2 * body_size) & 
                                    (lower_shadow < 0.1 * range_size)).astype(int)
        df_result['spinning_top'] = ((body_size < 0.3 * range_size) & 
                                   (upper_shadow > 0.1 * range_size) & 
                                   (lower_shadow > 0.1 * range_size)).astype(int)
        
        df_result['bullish_candle'] = (df_result[close_col] > df_result[open_col]).astype(int)
        df_result['bearish_candle'] = (df_result[close_col] < df_result[open_col]).astype(int)
        
        return df_result

class AdvancedFeatures:
    @staticmethod
    def add_volatility_features(df: pd.DataFrame, close_col: str = 'close',
                              high_col: str = 'high', low_col: str = 'low',
                              windows: List[int] = [5, 10, 20, 50]) -> pd.DataFrame:
        df_result = df.copy()
        
        returns = df_result[close_col].pct_change()
        
        for window in windows:
            df_result[f'volatility_{window}'] = returns.rolling(window).std() * np.sqrt(252)
            df_result[f'parkinson_vol_{window}'] = np.sqrt(
                252 / (4 * np.log(2)) * 
                (np.log(df_result[high_col] / df_result[low_col]) ** 2).rolling(window).mean()
            )
            
            df_result[f'garman_klass_vol_{window}'] = np.sqrt(
                252 * (
                    0.5 * (np.log(df_result[high_col] / df_result[low_col]) ** 2).rolling(window).mean() -
                    (2 * np.log(2) - 1) * (np.log(df_result[close_col] / df_result[close_col].shift(1)) ** 2).rolling(window).mean()
                )
            )
        
        df_result['vol_regime'] = (df_result['volatility_20'] > df_result['volatility_20'].rolling(50).mean()).astype(int)
        
        return df_result
    
    @staticmethod
    def add_momentum_features(df: pd.DataFrame, close_col: str = 'close',
                            volume_col: str = 'volume',
                            periods: List[int] = [1, 3, 5, 10, 21]) -> pd.DataFrame:
        df_result = df.copy()
        
        for period in periods:
            df_result[f'momentum_{period}'] = df_result[close_col].pct_change(period) * 100
            df_result[f'log_momentum_{period}'] = np.log(df_result[close_col] / df_result[close_col].shift(period)) * 100
            
            if volume_col in df_result.columns:
                df_result[f'volume_momentum_{period}'] = df_result[volume_col].pct_change(period) * 100
                df_result[f'price_volume_corr_{period}'] = (df_result[close_col].rolling(period).corr(df_result[volume_col]))
        
        return df_result

class DataProcessor:
    def __init__(self):
        self.tech_indicators = TechnicalIndicators()
        self.rolling_features = RollingFeatures()
        self.percentage_changes = PercentageChanges()
        self.pivot_points = PivotPoints()
        self.fibonacci = FibonacciLevels()
        self.price_transforms = PriceTransformations()
        self.advanced_features = AdvancedFeatures()
    
    def process_forex_data(self, df: pd.DataFrame, 
                          add_patterns: bool = True,
                          add_volatility: bool = True,
                          add_momentum: bool = True,
                          add_fibonacci: bool = False,
                          add_pivots: bool = False) -> pd.DataFrame:
        df_result = df.copy()
        
        df_result = self.price_transforms.add_basic_transformations(df_result)
        
        if add_patterns:
            df_result = self.price_transforms.add_price_patterns(df_result)
        
        if add_volatility:
            df_result = self.advanced_features.add_volatility_features(df_result)
        
        if add_momentum:
            df_result = self.advanced_features.add_momentum_features(df_result)
        
        if add_fibonacci:
            df_result = self.fibonacci.add_fibonacci_levels(df_result)
        
        if add_pivots:
            df_result = self.pivot_points.calculate_pivot_points(df_result)
        
        return df_result.fillna(method='ffill').fillna(0)