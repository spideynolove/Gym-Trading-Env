import pandas as pd
import numpy as np

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
    def calculate_pivot_points(
        df: pd.DataFrame, 
        suffix: str = '', 
        pivot_type: str = 'standard'
    ) -> pd.DataFrame:
        
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
                               pivot_points: list = ['S3', 'S2', 'S1', 'PP', 'R1', 'R2', 'R3'],
                               choices: list = None) -> np.ndarray:
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