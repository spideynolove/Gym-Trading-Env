import pandas as pd

class FibonacciLevels:
    STANDARD_LEVELS = (0.236, 0.382, 0.5, 0.618, 0.786)
    EXTENDED_LEVELS = (
        0.236, 0.382, 0.5, 0.618, 0.707, 0.786, 
        0.886, 1.382, 1.5, 1.618, 1.786, 1.886, 
        2.0, 2.618, 2.786, 2.886
    )
    IMPORTANT_LEVELS = (1.786, 1.886, 2.786, 2.886)
    
    @staticmethod
    def calculate_fib_levels(
        start: float, 
        end: float, 
        levels: list
    ) -> list:
        
        ratios = sorted([0.0] + levels + [1.0])
        level_prices = [round(start + ratio * (end - start), 6) for ratio in ratios]
        return level_prices[1:-1]
    
    @staticmethod
    def add_fibonacci_levels(
        df: pd.DataFrame, 
        high_col: str = 'high', 
        low_col: str = 'low',
        levels: list = None, 
        level_type: str = 'standard'
    ) -> pd.DataFrame:
        
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