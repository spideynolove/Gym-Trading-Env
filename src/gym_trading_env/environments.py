import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import numpy as np
import datetime
import glob
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional, Union
from .utils.history import History
from .utils.portfolio import Portfolio, TargetPortfolio
import os

# from collections import Counter
# import tempfile

import warnings

warnings.filterwarnings("error")


def basic_reward_function(history: History) -> float:
    """Log return reward function."""
    return np.log(history["portfolio_valuation", -1] / history["portfolio_valuation", -2])


def dynamic_feature_last_position_taken(history: History) -> float:
    """Returns the last position taken by the agent."""
    return history['position', -1]


def dynamic_feature_real_position(history: History) -> float:
    """Returns the real position of the portfolio (after price fluctuations)."""
    return history['real_position', -1]


class TradingEnv(gym.Env):
    """
    A flexible trading environment for OpenAI Gym.

    Recommended usage:
    >>> import gymnasium as gym
    >>> import gym_trading_env
    >>> env = gym.make('TradingEnv', ...)

    Args:
        df: Market data DataFrame with columns: 'open', 'high', 'low', 'close'. Index must be DatetimeIndex.
            Columns containing 'feature' in their name are used as observations.
        positions: List of allowed positions (e.g., [0, 1] for flat/long, [-1, 0, 1] for short/flat/long).
        dynamic_feature_functions: Functions that compute dynamic features at each step.
        reward_function: Function that takes the History object and returns a scalar reward.
        windows: Number of past observations to include in the observation space (for RNNs). If None, only current step is returned.
        trading_fees: Transaction fees as a fraction (e.g., 0.001 = 0.1%).
        borrow_interest_rate: Borrow interest rate per step (for leverage/shorting).
        portfolio_initial_value: Initial portfolio value in fiat.
        initial_position: Starting position ('random' or a value in `positions`).
        max_episode_duration: Maximum episode length in steps. If 'max', episodes run until end of data.
        verbose: Verbosity level (0 = silent, 1 = log results).
        name: Environment name (e.g., 'BTC/USDT').
        render_mode: Currently only 'logs' is supported.
    """

    metadata = {'render_modes': ['logs']}

    def __init__(
        self,
        df: pd.DataFrame,
        positions: List[Union[int, float]] = None,
        dynamic_feature_functions: List[Callable[[History], float]] = None,
        reward_function: Callable[[History], float] = basic_reward_function,
        windows: Optional[int] = None,
        trading_fees: float = 0.0,
        borrow_interest_rate: float = 0.0,
        portfolio_initial_value: float = 1000.0,
        initial_position: Union[str, float] = 'random',
        max_episode_duration: Union[int, str] = 'max',
        verbose: int = 1,
        name: str = "Stock",
        render_mode: Optional[str] = "logs"
    ):
        super().__init__()

        self.positions = positions or [0, 1]
        self.dynamic_feature_functions = dynamic_feature_functions or [
            dynamic_feature_last_position_taken,
            dynamic_feature_real_position
        ]
        self.reward_function = reward_function
        self.windows = windows
        self.trading_fees = trading_fees
        self.borrow_interest_rate = borrow_interest_rate
        self.portfolio_initial_value = float(portfolio_initial_value)
        self.initial_position = initial_position
        self.max_episode_duration = max_episode_duration
        self.verbose = verbose
        self.name = name

        assert self.initial_position in self.positions or self.initial_position == 'random', \
            "Initial position must be 'random' or in positions list."
        assert render_mode is None or render_mode in self.metadata["render_modes"], \
            f"Render mode must be in {self.metadata['render_modes']}"

        self.render_mode = render_mode
        self.log_metrics: List[Dict[str, Any]] = []
        self._set_df(df)

        # Define action and observation spaces
        self.action_space = spaces.Discrete(len(self.positions))
        obs_shape = (self._nb_features,) if self.windows is None else (self.windows, self._nb_features)
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=obs_shape, dtype=np.float32)

    def _set_df(self, df: pd.DataFrame) -> None:
        """Initialize internal data structures from DataFrame."""
        df = df.copy()
        self._features_columns = [col for col in df.columns if "feature" in col]
        self._info_columns = list(set(df.columns) | {"close"} - set(self._features_columns))
        self._nb_features = len(self._features_columns)
        self._nb_static_features = self._nb_features

        # Add dynamic feature columns
        for i, _ in enumerate(self.dynamic_feature_functions):
            col_name = f"dynamic_feature__{i}"
            df[col_name] = 0.0
            self._features_columns.append(col_name)
            self._nb_features += 1

        self.df = df
        self._obs_array = np.array(self.df[self._features_columns], dtype=np.float32)
        self._info_array = np.array(self.df[self._info_columns])
        self._price_array = np.array(self.df["close"])

    def _get_ticker(self, delta: int = 0) -> pd.Series:
        """Get ticker data at current index + delta."""
        return self.df.iloc[self._idx + delta]

    def _get_price(self, delta: int = 0) -> float:
        """Get price at current index + delta."""
        return self._price_array[self._idx + delta]

    def _get_obs(self) -> np.ndarray:
        """Get current observation."""
        # Update dynamic features
        for i, func in enumerate(self.dynamic_feature_functions):
            self._obs_array[self._idx, self._nb_static_features + i] = func(self.historical_info)

        if self.windows is None:
            idx = self._idx
        else:
            start_idx = max(0, self._idx + 1 - self.windows)
            idx = slice(start_idx, self._idx + 1)

        return self._obs_array[idx]

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
        **kwargs
    ) -> tuple[np.ndarray, dict]:
        """Reset environment to initial state."""
        super().reset(seed=seed)
        self._step = 0
        self._position = (
            np.random.choice(self.positions)
            if self.initial_position == 'random'
            else self.initial_position
        )
        self._limit_orders = {}
        self._idx = 0

        if self.windows is not None:
            self._idx = self.windows - 1

        if isinstance(self.max_episode_duration, int):
            low = self._idx
            high = len(self.df) - self.max_episode_duration - self._idx
            self._idx = np.random.randint(low=max(low, 0), high=max(high, low + 1))

        price = self._get_price()
        self._portfolio = TargetPortfolio(
            position=self._position,
            value=self.portfolio_initial_value,
            price=price
        )

        self.historical_info = History(max_size=len(self.df))
        self.historical_info.set(
            idx=self._idx,
            step=self._step,
            date=self.df.index.values[self._idx],
            position_index=self.positions.index(self._position),
            position=self._position,
            real_position=self._position,
            data=dict(zip(self._info_columns, self._info_array[self._idx])),
            portfolio_valuation=self.portfolio_initial_value,
            portfolio_distribution=self._portfolio.get_portfolio_distribution(),
            reward=0,
        )

        return self._get_obs(), self.historical_info[0]

    def render(self) -> None:
        """Render the environment (currently a no-op)."""
        pass

    def _trade(self, position: float, price: Optional[float] = None) -> None:
        """Execute a trade to target position."""
        current_price = self._get_price() if price is None else price
        self._portfolio.trade_to_position(
            position=position,
            price=current_price,
            trading_fees=self.trading_fees
        )
        self._position = position

    def _take_action(self, position: float) -> None:
        """Take action if different from current position."""
        if position != self._position:
            self._trade(position)

    def _take_action_order_limit(self) -> None:
        """Execute limit orders based on current market data."""
        if not self._limit_orders:
            return

        ticker = self._get_ticker()
        high, low = ticker["high"], ticker["low"]
        executed_positions = []

        for position, params in self._limit_orders.items():
            if (position != self._position and
                    params['limit'] <= high and
                    params['limit'] >= low):
                self._trade(position, price=params['limit'])
                if not params['persistent']:
                    executed_positions.append(position)

        for pos in executed_positions:
            del self._limit_orders[pos]

    def add_limit_order(self, position: float, limit: float, persistent: bool = False) -> None:
        """Add a limit order."""
        self._limit_orders[position] = {
            'limit': limit,
            'persistent': persistent
        }

    def step(self, action: Optional[int] = None) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Execute one time step within the environment."""
        # Take action
        if action is not None:
            self._take_action(self.positions[action])

        # Advance time
        self._idx += 1
        self._step += 1

        # Execute limit orders
        self._take_action_order_limit()

        # Update portfolio
        price = self._get_price()
        self._portfolio.update_interest(borrow_interest_rate=self.borrow_interest_rate)
        portfolio_value = self._portfolio.valorisation(price)
        portfolio_distribution = self._portfolio.get_portfolio_distribution()

        # Check termination conditions
        done = portfolio_value <= 0
        truncated = (
            self._idx >= len(self.df) - 1 or
            (isinstance(self.max_episode_duration, int) and self._step >= self.max_episode_duration - 1)
        )

        # Record step in history
        self.historical_info.add(
            idx=self._idx,
            step=self._step,
            date=self.df.index.values[self._idx],
            position_index=action,
            position=self._position,
            real_position=self._portfolio.real_position(price),
            data=dict(zip(self._info_columns, self._info_array[self._idx])),
            portfolio_valuation=portfolio_value,
            portfolio_distribution=portfolio_distribution,
            reward=0
        )

        # Compute reward
        reward = 0.0
        if not done:
            reward = self.reward_function(self.historical_info)
            self.historical_info["reward", -1] = reward

        # Finalize episode
        if done or truncated:
            self.calculate_metrics()
            self.log()

        return self._get_obs(), reward, done, truncated, self.historical_info[-1]

    def add_metric(self, name: str, function: Callable[[History], Any]) -> None:
        """Add a custom metric to be computed at episode end."""
        self.log_metrics.append({'name': name, 'function': function})

    def calculate_metrics(self) -> None:
        """Calculate performance metrics at episode end."""
        close_returns = self.historical_info['data_close', -1] / self.historical_info['data_close', 0] - 1
        portfolio_returns = (
            self.historical_info['portfolio_valuation', -1] /
            self.historical_info['portfolio_valuation', 0] - 1
        )

        self.results_metrics = {
            "Market Return": f"{100 * close_returns:5.2f}%",
            "Portfolio Return": f"{100 * portfolio_returns:5.2f}%",
        }

        for metric in self.log_metrics:
            try:
                self.results_metrics[metric['name']] = metric['function'](self.historical_info)
            except Exception as e:
                print(f"Error computing metric {metric['name']}: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get the latest computed metrics."""
        return self.results_metrics.copy()

    def log(self) -> None:
        """Log results if verbose mode is enabled."""
        if self.verbose > 0:
            text = " | ".join(f"{k}: {v}" for k, v in self.results_metrics.items())
            print(text)

    def save_for_render(self, dir_path: str = "render_logs") -> None:
        """Save environment data for later rendering."""
        required_cols = {"open", "high", "low", "close"}
        missing = required_cols - set(self.df.columns)
        assert not missing, f"DataFrame missing columns: {missing}"

        columns = [col for col in self.historical_info.columns if not col.startswith("date_")]
        history_df = pd.DataFrame([self.historical_info[c] for c in columns], columns=columns)
        history_df.set_index("date", inplace=True)
        history_df.sort_index(inplace=True)

        render_df = self.df.join(history_df, how="inner")

        os.makedirs(dir_path, exist_ok=True)
        filepath = f"{dir_path}/{self.name}_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.pkl"
        render_df.to_pickle(filepath)


class MultiDatasetTradingEnv(TradingEnv):
    """
    An extension of TradingEnv that cycles through multiple datasets.

    This helps reduce overfitting by exposing the agent to diverse market conditions.

    Example:
    >>> def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    ...     df["feature_close"] = df["close"].pct_change()
    ...     df["feature_volume"] = df["volume"] / df["volume"].rolling(7*24).max()
    ...     return df.dropna()
    ...
    >>> env = gym.make(
    ...     "MultiDatasetTradingEnv",
    ...     dataset_dir="data/*.pkl",
    ...     preprocess=preprocess
    ... )

    Args:
        dataset_dir: Glob pattern matching dataset files (e.g., 'data/*.pkl').
        preprocess: Function to apply to each dataset before use.
        episodes_between_dataset_switch: Number of episodes per dataset before switching.
        *args, **kwargs: Passed to TradingEnv constructor.
    """

    def __init__(
        self,
        dataset_dir: str,
        *args,
        preprocess: Callable[[pd.DataFrame], pd.DataFrame] = lambda df: df,
        episodes_between_dataset_switch: int = 1,
        **kwargs
    ):
        self.dataset_dir = dataset_dir
        self.preprocess = preprocess
        self.episodes_between_dataset_switch = episodes_between_dataset_switch
        self.dataset_pathes = glob.glob(dataset_dir)

        if not self.dataset_pathes:
            raise FileNotFoundError(f"No datasets found with pattern: {dataset_dir}")

        self.dataset_nb_uses = np.zeros(len(self.dataset_pathes))
        super().__init__(self.next_dataset(), *args, **kwargs)

    def next_dataset(self) -> pd.DataFrame:
        """Select the next dataset using round-robin with least-recently-used priority."""
        self._episodes_on_this_dataset = 0
        min_uses = self.dataset_nb_uses.min()
        candidates = np.where(self.dataset_nb_uses == min_uses)[0]
        selected_idx = np.random.choice(candidates)

        self.dataset_nb_uses[selected_idx] += 1
        dataset_path = self.dataset_pathes[selected_idx]
        self.name = Path(dataset_path).name

        if self.verbose > 1:
            print(f"Loading dataset: {self.name}")

        df = pd.read_pickle(dataset_path)
        return self.preprocess(df)

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
        **kwargs
    ) -> tuple[np.ndarray, dict]:
        """Reset environment, potentially loading a new dataset."""
        self._episodes_on_this_dataset += 1

        if self._episodes_on_this_dataset % self.episodes_between_dataset_switch == 0:
            new_df = self.next_dataset()
            self._set_df(new_df)

        return super().reset(seed=seed, options=options, **kwargs)