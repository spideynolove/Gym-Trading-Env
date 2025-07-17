import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

class RiskTrigger:
    def __init__(self, name: str):
        self.name = name
        self.triggered = False
    
    def check(self, history, current_position: float, portfolio_value: float) -> bool:
        raise NotImplementedError
    
    def reset(self):
        self.triggered = False

class StopLossTrigger(RiskTrigger):
    def __init__(self, stop_pct: float):
        super().__init__("stop_loss")
        self.stop_pct = stop_pct
        self.entry_value = None
        self.entry_position = None
    
    def check(self, history, current_position: float, portfolio_value: float) -> bool:
        if self.entry_value is None or self.entry_position != current_position:
            self.entry_value = portfolio_value
            self.entry_position = current_position
            return False
        
        if current_position != 0:
            loss_pct = (self.entry_value - portfolio_value) / self.entry_value
            if loss_pct >= self.stop_pct:
                self.triggered = True
                return True
        
        return False

class TakeProfitTrigger(RiskTrigger):
    def __init__(self, profit_pct: float):
        super().__init__("take_profit")
        self.profit_pct = profit_pct
        self.entry_value = None
        self.entry_position = None
    
    def check(self, history, current_position: float, portfolio_value: float) -> bool:
        if self.entry_value is None or self.entry_position != current_position:
            self.entry_value = portfolio_value
            self.entry_position = current_position
            return False
        
        if current_position != 0:
            profit_pct = (portfolio_value - self.entry_value) / self.entry_value
            if profit_pct >= self.profit_pct:
                self.triggered = True
                return True
        
        return False

class MaxDrawdownTrigger(RiskTrigger):
    def __init__(self, threshold: float):
        super().__init__("max_drawdown")
        self.threshold = threshold
        self.peak_value = None
    
    def check(self, history, current_position: float, portfolio_value: float) -> bool:
        if self.peak_value is None:
            self.peak_value = portfolio_value
            return False
        
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        
        drawdown = (self.peak_value - portfolio_value) / self.peak_value
        if drawdown >= self.threshold:
            self.triggered = True
            return True
        
        return False

class PositionLimitTrigger(RiskTrigger):
    def __init__(self, max_position: float):
        super().__init__("position_limit")
        self.max_position = max_position
    
    def check(self, history, current_position: float, portfolio_value: float) -> bool:
        if abs(current_position) > self.max_position:
            self.triggered = True
            return True
        return False

class RiskManager:
    def __init__(self, triggers: list = None):
        self.triggers = triggers or []
        self.active_triggers = []
    
    def add_trigger(self, trigger: RiskTrigger):
        self.triggers.append(trigger)
    
    def check_triggers(self, history, current_position: float, portfolio_value: float) -> Dict[str, bool]:
        results = {}
        
        for trigger in self.triggers:
            triggered = trigger.check(history, current_position, portfolio_value)
            results[trigger.name] = triggered
            
            if triggered and trigger not in self.active_triggers:
                self.active_triggers.append(trigger)
        
        return results
    
    def reset_triggers(self):
        for trigger in self.triggers:
            trigger.reset()
        self.active_triggers = []
    
    def get_exit_action(self) -> int:
        if self.active_triggers:
            return 0
        return None

def fixed_fraction_size(account_value: float, risk_fraction: float) -> float:
    return account_value * risk_fraction

def volatility_position_size(account_value: float, atr: float, atr_multiplier: float = 1.0, price: float = 1.0) -> float:
    dollar_volatility = atr * atr_multiplier * price
    if dollar_volatility == 0:
        return 0
    return account_value / dollar_volatility

def kelly_position_size(win_rate: float, payoff_ratio: float, safety_factor: float = 0.25) -> float:
    if payoff_ratio <= 0:
        return 0
    b = payoff_ratio
    p = win_rate
    q = 1 - p
    kelly_fraction = max(0.0, (b * p - q) / b)
    return kelly_fraction * safety_factor

def capped_position_size(position: float, max_percent: float) -> float:
    return min(position, max_percent)