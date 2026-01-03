import datetime
import glob
import os
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces

from .utils.history import History
from .utils.portfolio import Portfolio, TargetPortfolio

warnings.filterwarnings("error")


def basic_reward_function(history: History) -> float:
    return np.log(
        history["portfolio_valuation", -1] / history["portfolio_valuation", -2]
    )


def dynamic_feature_last_position_taken(history: History) -> float:
    return history["position", -1]


def dynamic_feature_real_position(history: History) -> float:
    return history["real_position", -1]


class TradingEnv(gym.Env):
    metadata = {"render_modes": ["logs"]}

    def __init__(
        self,
        df: pd.DataFrame,
        positions: Optional[List[Union[int, float]]] = None,
        dynamic_feature_functions: Optional[
            List[Callable[[History], float]]
        ] = None,
        reward_function: Callable[[History], float] = basic_reward_function,
        windows: Optional[int] = None,
        trading_fees: float = 0.0,
        borrow_interest_rate: float = 0.0,
        portfolio_initial_value: float = 1000.0,
        initial_position: Union[str, float] = "random",
        max_episode_duration: Union[int, str] = "max",
        verbose: int = 1,
        name: str = "Stock",
        render_mode: Optional[str] = "logs",
    ):
        super().__init__()
        self.positions = positions or [0, 1]
        self.dynamic_feature_functions = dynamic_feature_functions or [
            dynamic_feature_last_position_taken,
            dynamic_feature_real_position,
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
        self.log_metrics: List[Dict[str, Any]] = []

        if self.initial_position not in self.positions and self.initial_position != "random":
            raise ValueError("Initial position must be 'random' or in positions list.")

        if render_mode is not None and render_mode not in self.metadata["render_modes"]:
            raise ValueError(f"Render mode must be in {self.metadata['render_modes']}")

        self.render_mode = render_mode
        self._set_df(df)

        self.action_space = spaces.Discrete(len(self.positions))
        obs_shape = (
            (self._nb_features,)
            if self.windows is None
            else (self.windows, self._nb_features)
        )
        self.observation_space = spaces.Box(
            -np.inf, np.inf, shape=obs_shape, dtype=np.float32
        )

    def _set_df(self, df: pd.DataFrame) -> None:
        df = df.copy()
        self._features_columns = [
            col for col in df.columns if "feature" in col
        ]
        self._info_columns = list(
            set(df.columns) | {"close"} - set(self._features_columns)
        )
        self._nb_features = len(self._features_columns)
        self._nb_static_features = self._nb_features

        for i, _ in enumerate(self.dynamic_feature_functions):
            col_name = f"dynamic_feature__{i}"
            df[col_name] = 0.0
            self._features_columns.append(col_name)
            self._nb_features += 1

        self.df = df
        self._obs_array = self.df[self._features_columns].values.astype(np.float32)
        self._info_array = self.df[self._info_columns].values
        self._price_array = self.df["close"].values

    def _get_ticker(self, delta: int = 0) -> pd.Series:
        return self.df.iloc[self._idx + delta]

    def _get_price(self, delta: int = 0) -> float:
        return self._price_array[self._idx + delta]

    def _get_obs(self) -> np.ndarray:
        for i, func in enumerate(self.dynamic_feature_functions):
            self._obs_array[
                self._idx, self._nb_static_features + i
            ] = func(self.historical_info)

        if self.windows is None:
            idx = self._idx
        else:
            start_idx = max(0, self._idx + 1 - self.windows)
            idx = slice(start_idx, self._idx + 1)
        return self._obs_array[idx]

    def reset(
        self, seed: Optional[int] = None, options: Optional[dict] = None, **kwargs
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self._step = 0
        self._position = (
            np.random.choice(self.positions)
            if self.initial_position == "random"
            else self.initial_position
        )
        self._limit_orders = {}
        self._idx = 0
        if self.windows is not None:
            self._idx = self.windows - 1
        if isinstance(self.max_episode_duration, int):
            low = self._idx
            high = len(self.df) - self.max_episode_duration - self._idx
            self._idx = np.random.randint(
                low=max(low, 0), high=max(high, low + 1)
            )

        price = self._get_price()
        self._portfolio = TargetPortfolio(
            position=self._position,
            value=self.portfolio_initial_value,
            price=price,
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
        pass

    def _trade(self, position: float, price: Optional[float] = None) -> None:
        current_price = self._get_price() if price is None else price
        self._portfolio.trade_to_position(
            position=position, price=current_price, trading_fees=self.trading_fees
        )
        self._position = position

    def _take_action(self, position: float) -> None:
        if position != self._position:
            self._trade(position)

    def _take_action_order_limit(self) -> None:
        if not self._limit_orders:
            return

        ticker = self._get_ticker()
        high, low = ticker["high"], ticker["low"]

        executed_positions = [
            position
            for position, params in self._limit_orders.items()
            if position != self._position
            and params["limit"] <= high
            and params["limit"] >= low
        ]

        for position in executed_positions:
            params = self._limit_orders[position]
            self._trade(position, price=params["limit"])
            if not params["persistent"]:
                del self._limit_orders[position]


    def add_limit_order(
        self, position: float, limit: float, persistent: bool = False
    ) -> None:
        self._limit_orders[position] = {
            "limit": limit, "persistent": persistent
        }

    def step(
        self, action: Optional[int] = None
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        if action is not None:
            self._take_action(self.positions[action])

        self._idx += 1
        self._step += 1
        self._take_action_order_limit()

        price = self._get_price()
        self._portfolio.update_interest(borrow_interest_rate=self.borrow_interest_rate)
        portfolio_value = self._portfolio.valorisation(price)
        portfolio_distribution = self._portfolio.get_portfolio_distribution()

        done = portfolio_value <= 0
        truncated = self._idx >= len(self.df) - 1 or (
            isinstance(self.max_episode_duration, int)
            and self._step >= self.max_episode_duration - 1
        )

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
            reward=0,
        )

        reward = 0.0
        if not done:
            reward = self.reward_function(self.historical_info)
            self.historical_info["reward", -1] = reward

        if done or truncated:
            self.calculate_metrics()
            self.log()

        return self._get_obs(), reward, done, truncated, self.historical_info[-1]

    def add_metric(self, name: str, function: Callable[[History], Any]) -> None:
        self.log_metrics.append({"name": name, "function": function})

    def calculate_metrics(self) -> None:
        close_returns = (
            self.historical_info["data_close", -1]
            / self.historical_info["data_close", 0]
            - 1
        )
        portfolio_returns = (
            self.historical_info["portfolio_valuation", -1]
            / self.historical_info["portfolio_valuation", 0]
            - 1
        )

        self.results_metrics = {
            "Market Return": f"{100 * close_returns:5.2f}%",
            "Portfolio Return": f"{100 * portfolio_returns:5.2f}%",
        }

        for metric in self.log_metrics:
            try:
                self.results_metrics[metric["name"]] = metric["function"](
                    self.historical_info
                )
            except Exception as e:
                print(f"Error computing metric {metric['name']}: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        return self.results_metrics.copy()

    def log(self) -> None:
        if self.verbose > 0:
            text = " | ".join(
                f"{k}: {v}" for k, v in self.results_metrics.items()
            )
            print(text)

    def save_for_render(self, dir_path: str = "render_logs") -> None:
        required_cols = {"open", "high", "low", "close"}
        missing = required_cols - set(self.df.columns)
        if missing:
            raise ValueError(f"DataFrame missing columns: {missing}")

        columns = [
            col
            for col in self.historical_info.columns
            if not col.startswith("date_")
        ]
        history_df = pd.DataFrame(
            [self.historical_info[c] for c in columns], columns=columns
        )
        history_df.set_index("date", inplace=True)
        history_df.sort_index(inplace=True)

        render_df = self.df.join(history_df, how="inner")

        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        filepath = dir_path / f"{self.name}_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.pkl"
        render_df.to_pickle(filepath)


class MultiDatasetTradingEnv(TradingEnv):
    def __init__(
        self,
        dataset_dir: str,
        *args,
        preprocess: Callable[[pd.DataFrame], pd.DataFrame] = lambda df: df,
        episodes_between_dataset_switch: int = 1,
        **kwargs,
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
        self, seed: Optional[int] = None, options: Optional[dict] = None, **kwargs
    ) -> tuple[np.ndarray, dict]:
        self._episodes_on_this_dataset += 1
        if self._episodes_on_this_dataset % self.episodes_between_dataset_switch == 0:
            new_df = self.next_dataset()
            self._set_df(new_df)
        return super().reset(seed=seed, options=options, **kwargs)
