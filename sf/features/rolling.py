import pandas as pd

class RollingFeatures:
    SUPPORTED_FUNCTIONS = (
        'mean', 'sum', 'max', 'min', 
        'var', 'std', 'skew', 'kurt', 
        'shift', 'diff'
    )
    
    @staticmethod
    def add_rolling_functions(
        df: pd.DataFrame, 
        column_names: list, 
        window_sizes: list, 
        functions: list
    ) -> pd.DataFrame:
        
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