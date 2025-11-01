import pandas as pd
import sys

class LazyCallable:
    def __init__(self, name):
        self.n, self.f = name, None
    
    def __call__(self, *a, **k):
        if self.f is None:
            modn, funcn = self.n.rsplit('.', 1)
            if modn not in sys.modules:
                __import__(modn)
            self.f = getattr(sys.modules[modn], funcn)
        return self.f(*a, **k)

class TechnicalIndicators:
    @staticmethod
    def add_technical_indicators(
        df: pd.DataFrame, 
        indicators: dict
    ) -> pd.DataFrame:
        
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