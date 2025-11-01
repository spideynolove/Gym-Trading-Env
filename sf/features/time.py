import pandas as pd

class TimeBasedFeatures:
    @staticmethod
    def add_time_features(df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
        df_result = df.copy()
        
        df_result['hour'] = df_result[timestamp_col].dt.hour
        df_result['day_of_week'] = df_result[timestamp_col].dt.dayofweek
        df_result['month'] = df_result[timestamp_col].dt.month
        df_result['is_weekend'] = (df_result['day_of_week'] >= 5).astype(int)
        
        df_result['trading_session'] = pd.cut(df_result['hour'], bins=[0, 8, 16, 24], 
                                            labels=['Asian', 'European', 'American'], include_lowest=True)
        
        return df_result