import pandas as pd

class PriceTransformations:
    @staticmethod
    def add_basic_transformations(
        df: pd.DataFrame, 
        open_col: str = 'open',
        high_col: str = 'high', 
        low_col: str = 'low',
        close_col: str = 'close',
        volume_col: str = 'volume'
    ) -> pd.DataFrame:
    
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
    def add_price_patterns(
        df: pd.DataFrame,
        open_col: str = 'open', 
        high_col: str = 'high',
        low_col: str = 'low', 
        close_col: str = 'close'
    ) -> pd.DataFrame:
        
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