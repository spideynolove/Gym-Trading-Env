import pandas as pd
import numpy as np

class AdvancedFeatures:
    @staticmethod
    def calculate_close_to_close_volatility(
        df, 
        close_col='close', 
        windows=[30], 
        trading_periods=[252], 
        clean=False
    ) -> pd.DataFrame:
        
        df_result = df.copy()
        for trading_period in trading_periods:
            for window in windows:
                df_result[f'log_return_{trading_period}_{window}'] = np.log(df_result[close_col] / df_result[close_col].shift(1))
                df_result[f'c_vol_{trading_period}_{window}'] = df_result[f'log_return_{trading_period}_{window}'].rolling(window=window).std() * np.sqrt(trading_period) * 100
                df_result.drop(columns=[f'log_return_{trading_period}_{window}'], inplace=True)
        if clean:
            df_result = df_result.dropna()
        return df_result

    @staticmethod
    def calculate_parkinson_volatility(
        df, 
        high_col='high', 
        low_col='low', 
        windows=[30], 
        trading_periods=[252], 
        clean=False
    ) -> pd.DataFrame:
        
        df_result = df.copy()
        for trading_period in trading_periods:
            for window in windows:
                rs = (1.0 / (4.0 * np.log(2.0))) * ((df_result[high_col] / df_result[low_col]).apply(np.log)) ** 2.0
                def f(v):
                    return (trading_period * v.mean()) ** 0.5
                result_name = f'p_vol_{trading_period}_{window}'
                
                if len(df_result) < window:
                    df_result[result_name] = np.nan
                    continue                
                
                df_result[result_name] = rs.rolling(window=window, center=False).apply(func=f) * 100
        if clean:
            df_result = df_result.dropna()
        return df_result

    @staticmethod
    def calculate_garman_klass_volatility(
        df, 
        high_col='high', 
        low_col='low', 
        close_col='close', 
        open_col='open', 
        windows=[30], 
        trading_periods=[252], 
        clean=False
    ) -> pd.DataFrame:

        df_result = df.copy()
        for trading_period in trading_periods:
            for window in windows:
                log_hl = np.log(df_result[high_col] / df_result[low_col])
                log_co = np.log(df_result[close_col] / df_result[open_col])
                rs = 0.5 * log_hl ** 2 - (2 * np.log(2) - 1) * log_co ** 2
                def f(v):
                    return (trading_period * v.mean()) ** 0.5
                result_col_name = f'gk_vol_{trading_period}_{window}'
                
                if len(df_result) < window:
                    df_result[result_col_name] = np.nan
                    continue

                df_result[result_col_name] = rs.rolling(window=window, center=False).apply(func=f) * 100
        if clean:
            df_result = df_result.dropna()
        return df_result

    @staticmethod
    def calculate_hodges_tompkins_volatility(
        df, 
        close_col='close', 
        windows=[30], 
        trading_periods=[252], 
        clean=False
    ) -> pd.DataFrame:
        
        df_result = df.copy()
        for trading_period in trading_periods:
            for window in windows:
                log_return = np.log(df_result[close_col] / df_result[close_col].shift(1))
                vol = log_return.rolling(window=window, center=False).std() * np.sqrt(trading_period)
                h = window
                
                n = (log_return.count() - h) + 1
                if n <= h or n <= 0:
                    df_result[f'ht_vol_{trading_period}_{window}'] = np.nan
                    continue
                adj_factor = 1.0 / (1.0 - (h / n) + ((h ** 2 - 1) / (3 * n ** 2)))
                
                df_result[f'ht_vol_{trading_period}_{window}'] = vol * adj_factor * 100
        if clean:
            df_result = df_result.dropna()
        return df_result

    @staticmethod
    def calculate_rogers_satchell_volatility(
        df, 
        high_col='high', 
        low_col='low',
        close_col='close',
        open_col='open',
        windows=[30],
        trading_periods=[252],
        clean=False
    ) -> pd.DataFrame:
        
        df_result = df.copy()
        for trading_period in trading_periods:
            for window in windows:
                log_ho = np.log(df_result[high_col] / df_result[open_col])
                log_lo = np.log(df_result[low_col] / df_result[open_col])
                log_co = np.log(df_result[close_col] / df_result[open_col])
                rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
                def f(v):
                    return (trading_period * v.mean()) ** 0.5
                
                if len(df_result) < window:
                    df_result[f'rs_vol_{trading_period}_{window}'] = np.nan
                    continue                
                
                df_result[f'rs_vol_{trading_period}_{window}'] = rs.rolling(window=window, center=False).apply(func=f) * 100
        if clean:
            df_result = df_result.dropna()
        return df_result

    @staticmethod
    def calculate_yang_zhang_volatility(
        df, 
        high_col='high', 
        low_col='low',
        close_col='close',
        open_col='open',
        windows=[30],
        trading_periods=[252],
        clean=False
    ) -> pd.DataFrame:
        
        df_result = df.copy()
        for trading_period in trading_periods:
            for window in windows:
                log_ho = np.log(df_result[high_col] / df_result[open_col])
                log_lo = np.log(df_result[low_col] / df_result[open_col])
                log_co = np.log(df_result[close_col] / df_result[open_col])
                
                log_oc = np.log(df_result[open_col] / df_result[close_col].shift(1))
                log_oc_sq = log_oc ** 2
                
                log_cc = np.log(df_result[close_col] / df_result[close_col].shift(1))
                log_cc_sq = log_cc ** 2
                
                rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
                
                close_vol = log_cc_sq.rolling(window=window, center=False).sum() * (1.0 / (window - 1.0))
                open_vol = log_oc_sq.rolling(window=window, center=False).sum() * (1.0 / (window - 1.0))
                window_rs = rs.rolling(window=window, center=False).sum() * (1.0 / (window - 1.0))
                
                k = 0.34 / (1.34 + (window + 1) / (window - 1))
                
                if len(df_result) < window + 1:
                    df_result[f'yz_vol_{trading_period}_{window}'] = np.nan
                    continue                
                
                df_result[f'yz_vol_{trading_period}_{window}'] = (open_vol + k * close_vol + (1 - k) * window_rs).apply(np.sqrt) * np.sqrt(trading_period) * 100
        if clean:
            df_result = df_result.dropna()
        return df_result

    @staticmethod
    def add_volatility_features(
        df: pd.DataFrame, 
        close_col: str = 'close',
        high_col: str = 'high', 
        low_col: str = 'low', 
        open_col: str = 'open',
        windows: list = [5, 10, 20, 50]
    ) -> pd.DataFrame:
        
        df_result = df.copy()
        
        returns = df_result[close_col].pct_change()
        
        for window in windows:
            df_result[f'volatility_{window}'] = returns.rolling(window).std() * np.sqrt(252)
        
        df_result = AdvancedFeatures.calculate_parkinson_volatility(df_result, high_col, low_col, windows)
        df_result = AdvancedFeatures.calculate_garman_klass_volatility(df_result, high_col, low_col, close_col, open_col, windows)
        df_result = AdvancedFeatures.calculate_close_to_close_volatility(df_result, close_col, windows)
        df_result = AdvancedFeatures.calculate_hodges_tompkins_volatility(df_result, close_col, windows)
        df_result = AdvancedFeatures.calculate_rogers_satchell_volatility(df_result, high_col, low_col, close_col, open_col, windows)
        df_result = AdvancedFeatures.calculate_yang_zhang_volatility(df_result, high_col, low_col, close_col, open_col, windows)
        
        df_result['vol_regime'] = (df_result['volatility_20'] > df_result['volatility_20'].rolling(50).mean()).astype(int)
        
        return df_result

    @staticmethod
    def add_momentum_features(
        df: pd.DataFrame,
        close_col: str = 'close',
        volume_col: str = 'volume',
        periods: list = [1, 3, 5, 10, 21]
    ) -> pd.DataFrame:
        
        df_result = df.copy()
        
        for period in periods:
            df_result[f'momentum_{period}'] = df_result[close_col].pct_change(periods=period) * 100
            df_result[f'roc_{period}'] = ((df_result[close_col] / df_result[close_col].shift(period)) - 1) * 100
            
            if volume_col in df_result.columns:
                df_result[f'volume_momentum_{period}'] = df_result[volume_col].pct_change(periods=period) * 100
        
        return df_result