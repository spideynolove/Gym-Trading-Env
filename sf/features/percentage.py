import pandas as pd

class PercentageChanges:
    PERIOD_MAP = {'W': 5, 'M': 21, 'Q': 63, 'Y': 252, '3Y': 756}
    
    @staticmethod
    def add_percentage_change(
        df: pd.DataFrame, 
        column_name: str, 
        periods: list
    ) -> pd.DataFrame:
        
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