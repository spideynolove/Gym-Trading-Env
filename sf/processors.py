import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from .features import (
    TechnicalIndicators, RollingFeatures, PercentageChanges, 
    PivotPoints, FibonacciLevels, PriceTransformations,
    AdvancedFeatures, TimeBasedFeatures, CategoricalFeatures
)

class DataProcessor:
    def __init__(self, config_path=None):
        self.tech_indicators = TechnicalIndicators()
        self.rolling_features = RollingFeatures()
        self.percentage_changes = PercentageChanges()
        self.pivot_points = PivotPoints()
        self.fibonacci = FibonacciLevels()
        self.price_transforms = PriceTransformations()
        self.advanced_features = AdvancedFeatures()
        self.time_features = TimeBasedFeatures()
        self.categorical_features = CategoricalFeatures()
        
        self.config = self.load_config(config_path) if config_path else {}
    
    def load_config(self, config_path):
        if isinstance(config_path, (str, Path)):
            with open(config_path, 'r') as f:
                return json.load(f)
        elif isinstance(config_path, dict):
            return config_path
        return {}
    
    def process_dataframe(self, df, 
                        add_patterns=True,
                        add_volatility=True,
                        add_momentum=True,
                        add_fibonacci=False,
                        add_pivots=False,
                        add_time_features=True,
                        add_categorical=True):
        df_result = df.copy()
        
        if 'technical_indicators' in self.config:
            df_result = self.tech_indicators.add_technical_indicators(
                df_result, self.config['technical_indicators']
            )
        
        if 'rolling_features' in self.config:
            config = self.config['rolling_features']
            df_result = self.rolling_features.add_rolling_functions(
                df_result, 
                config.get('columns', ['close']),
                config.get('windows', [20]),
                config.get('functions', ['mean'])
            )
        
        if 'percentage_changes' in self.config:
            config = self.config['percentage_changes']
            for column, periods in config.items():
                df_result = self.percentage_changes.add_percentage_change(
                    df_result, column, periods
                )
        
        if 'pivot_points' in self.config or add_pivots:
            config = self.config.get('pivot_points', {})
            df_result = self.pivot_points.calculate_pivot_points(
                df_result,
                suffix=config.get('suffix', ''),
                pivot_type=config.get('type', 'standard')
            )
        
        if 'fibonacci' in self.config or add_fibonacci:
            config = self.config.get('fibonacci', {})
            df_result = self.fibonacci.add_fibonacci_levels(
                df_result,
                high_col=config.get('high_col', 'high'),
                low_col=config.get('low_col', 'low'),
                levels=config.get('levels'),
                level_type=config.get('level_type', 'standard')
            )
        
        if 'price_transforms' in self.config:
            config = self.config['price_transforms']
            if config.get('basic', True):
                df_result = self.price_transforms.add_basic_transformations(
                    df_result,
                    open_col=config.get('open_col', 'open'),
                    high_col=config.get('high_col', 'high'),
                    low_col=config.get('low_col', 'low'),
                    close_col=config.get('close_col', 'close'),
                    volume_col=config.get('volume_col', 'volume')
                )
            if config.get('patterns', False) or add_patterns:
                df_result = self.price_transforms.add_price_patterns(
                    df_result,
                    open_col=config.get('open_col', 'open'),
                    high_col=config.get('high_col', 'high'),
                    low_col=config.get('low_col', 'low'),
                    close_col=config.get('close_col', 'close')
                )
        else:
            df_result = self.price_transforms.add_basic_transformations(df_result)
            if add_patterns:
                df_result = self.price_transforms.add_price_patterns(df_result)
        
        if 'advanced_features' in self.config:
            config = self.config['advanced_features']
            if config.get('volatility', False) or add_volatility:
                df_result = self.advanced_features.add_volatility_features(
                    df_result,
                    close_col=config.get('close_col', 'close'),
                    high_col=config.get('high_col', 'high'),
                    low_col=config.get('low_col', 'low'),
                    windows=config.get('windows', [5, 10, 20, 50])
                )
            if config.get('momentum', False) or add_momentum:
                df_result = self.advanced_features.add_momentum_features(
                    df_result,
                    close_col=config.get('close_col', 'close'),
                    volume_col=config.get('volume_col', 'volume'),
                    periods=config.get('periods', [1, 3, 5, 10, 21])
                )
        else:
            if add_volatility:
                df_result = self.advanced_features.add_volatility_features(df_result)
            if add_momentum:
                df_result = self.advanced_features.add_momentum_features(df_result)

        if add_time_features and 'timestamp' in df_result.columns:
            df_result = self.time_features.add_time_features(df_result)
        
        if add_categorical:
            df_result = self.categorical_features.add_features(df_result)      
        
        return df_result.ffill().fillna(0)