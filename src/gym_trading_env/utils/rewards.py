import numpy as np

def safe_log_return(history, floor: float = 1e-4, clip_range: tuple = (-1.0, 1.0)) -> float:
    if len(history) < 2:
        return 0.0
    
    try:
        v_t = max(history['portfolio_valuation', -1], floor)
        v_t_1 = max(history['portfolio_valuation', -2], floor)
    except (IndexError, KeyError):
        return 0.0
    
    log_r = np.log(v_t / v_t_1)
    return np.clip(log_r, *clip_range)

def sharpe_like_reward(history, window: int = 10, min_periods: int = 2) -> float:
    if len(history) < max(window, min_periods):
        return 0.0
    
    try:
        portfolio_values = history['portfolio_valuation']
        if len(portfolio_values) < window:
            return 0.0
        
        recent_values = portfolio_values[-window:]
        returns = np.diff(recent_values) / recent_values[:-1]
        
        if len(returns) < min_periods:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        return mean_return / std_return if std_return > 0 else 0.0
    except (IndexError, KeyError, ValueError):
        return 0.0

def reward_with_trading_penalty(base_reward: float, n_trades: int, penalty_per_trade: float = 0.001) -> float:
    penalty = n_trades * penalty_per_trade
    return base_reward - penalty

def drawdown_penalty(history, max_drawdown: float = 0.20) -> float:
    if len(history) < 2:
        return 0.0
    
    try:
        portfolio_values = history['portfolio_valuation']
        if len(portfolio_values) < 2:
            return 0.0
        
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak
        current_drawdown = drawdown[-1]
        
        if current_drawdown > max_drawdown:
            return -current_drawdown * 10
        return 0.0
    except (IndexError, KeyError, ValueError):
        return 0.0

def safe_portfolio_return(history, floor: float = 1e-4) -> float:
    if len(history) < 2:
        return 0.0
    
    try:
        current_value = max(history['portfolio_valuation', -1], floor)
        initial_value = max(history['portfolio_valuation', 0], floor)
        return (current_value - initial_value) / initial_value
    except (IndexError, KeyError):
        return 0.0

def combined_reward(history, 
                   log_weight: float = 0.7, 
                   sharpe_weight: float = 0.2, 
                   drawdown_weight: float = 0.1,
                   trading_penalty: float = 0.001) -> float:
    log_reward = safe_log_return(history)
    sharpe_reward = sharpe_like_reward(history)
    dd_penalty = drawdown_penalty(history)
    
    try:
        n_trades = len([i for i in range(1, len(history)) 
                       if history['position', i] != history['position', i-1]])
    except (IndexError, KeyError):
        n_trades = 0
    
    base_reward = (log_weight * log_reward + 
                  sharpe_weight * sharpe_reward + 
                  drawdown_weight * dd_penalty)
    
    return reward_with_trading_penalty(base_reward, n_trades, trading_penalty)