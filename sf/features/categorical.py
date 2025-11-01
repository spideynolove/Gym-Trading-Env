import pandas as pd
import numpy as np

class CategoricalFeatures:
    def __init__(self, config: list = None):
        self.config = config or self._get_default_config()
    
    def _get_default_config(self):
        return [
            {
                'name': 'price_trend',
                'method': 'cut',
                'source_column': 'close_change',
                'bins': [-np.inf, -0.5, 0.5, np.inf],
                'labels': ['Down', 'Flat', 'Up'],
                'active': True
            },
            {
                'name': 'volatility_level',
                'method': 'qcut',
                'source_column': 'volatility_20',
                'bins': 3,
                'labels': ['Low', 'Medium', 'High'],
                'active': True
            },
            {
                'name': 'volume_level',
                'method': 'cut',
                'source_column': 'volume_ratio',
                'bins': [0, 0.8, 1.2, np.inf],
                'labels': ['Low', 'Normal', 'High'],
                'active': True
            }
        ]
    
    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df_result = df.copy()
        
        for feature_config in self.config:
            if not feature_config.get('active', True):
                continue
            
            feature_name = feature_config['name']
            method = feature_config.get('method', 'cut')
            source_col = feature_config.get('source_column')
            custom_func = feature_config.get('function')
            
            if method == 'custom' and custom_func:
                try:
                    df_result[feature_name] = custom_func(df_result)
                except Exception:
                    df_result[feature_name] = pd.NA
            elif source_col in df_result.columns:
                source_data = df_result[source_col]
                if source_data.nunique() > 1 and source_data.notna().sum() > 0:
                    try:
                        bins = feature_config.get('bins')
                        labels = feature_config.get('labels')
                        
                        if method == 'cut':
                            df_result[feature_name] = pd.cut(source_data, bins=bins, labels=labels, duplicates='drop')
                        elif method == 'qcut':
                            df_result[feature_name] = pd.qcut(source_data, q=bins, labels=labels, duplicates='drop')
                    except Exception:
                        df_result[feature_name] = labels[len(labels)//2] if labels else pd.NA
                else:
                    df_result[feature_name] = pd.NA
        
        df_result = df_result.ffill()

        for col in df_result.columns:
            if df_result[col].dtype.name == 'category':
                df_result[col] = df_result[col].cat.add_categories([0]).fillna(0)
            else:
                df_result[col] = df_result[col].fillna(0).infer_objects(copy=False)

        return df_result