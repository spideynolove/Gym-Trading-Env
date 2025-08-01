import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import numpy as np
import datetime
import glob
from pathlib import Path
from .utils.history import History
from .utils.sessions import SessionManager
# from .utils.news import NewsManager
from .utils.portfolio import TargetPortfolio    # Portfolio, 
import os
import warnings
warnings.filterwarnings('error')
def basic_reward_function(history: History):
    return np.log(history['portfolio_valuation', -1] / history[
        'portfolio_valuation', -2])
def dynamic_feature_last_position_taken(history):
    return history['position', -1]
def dynamic_feature_real_position(history):
    return history['real_position', -1]
class TradingEnv(gym.Env):
    metadata = {'render_modes': ['logs']}
    def __init__(self, df: pd.DataFrame, positions: list=[0, 1],
        dynamic_feature_functions=[dynamic_feature_last_position_taken,
        dynamic_feature_real_position], reward_function=
        basic_reward_function, windows=None, trading_fees=0,
        borrow_interest_rate=0, portfolio_initial_value=1000,
        initial_position='random', max_episode_duration='max', verbose=1,
        name='Stock', render_mode='logs'):
        self.max_episode_duration = max_episode_duration
        self.name = name
        self.verbose = verbose
        self.positions = positions
        self.dynamic_feature_functions = dynamic_feature_functions
        self.reward_function = reward_function
        self.windows = windows
        self.trading_fees = trading_fees
        self.borrow_interest_rate = borrow_interest_rate
        self.portfolio_initial_value = float(portfolio_initial_value)
        self.initial_position = initial_position
        assert self.initial_position in self.positions or self.initial_position == 'random', "The 'initial_position' parameter must be 'random' or a position mentionned in the 'position' (default is [0, 1]) parameter."
        assert render_mode is None or render_mode in self.metadata[
            'render_modes']
        self.max_episode_duration = max_episode_duration
        self.render_mode = render_mode
        self._set_df(df)
        self.action_space = spaces.Discrete(len(positions))
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=[self.
            _nb_features])
        if self.windows is not None:
            self.observation_space = spaces.Box(-np.inf, np.inf, shape=[
                self.windows, self._nb_features])
        self.log_metrics = []
    def _set_df(self, df):
        df = df.copy()
        self._features_columns = [col for col in df.columns if 'feature' in col
            ]
        self._info_columns = list(set(list(df.columns) + ['close']) - set(
            self._features_columns))
        self._nb_features = len(self._features_columns)
        self._nb_static_features = self._nb_features
        for i in range(len(self.dynamic_feature_functions)):
            df[f'dynamic_feature__{i}'] = 0
            self._features_columns.append(f'dynamic_feature__{i}')
            self._nb_features += 1
        self.df = df
        self._obs_array = np.array(self.df[self._features_columns], dtype=
            np.float32)
        self._info_array = np.array(self.df[self._info_columns])
        self._price_array = np.array(self.df['close'])
    def _get_ticker(self, delta=0):
        return self.df.iloc[self._idx + delta]
    def _get_price(self, delta=0):
        return self._price_array[self._idx + delta]
    def _get_obs(self):
        for i, dynamic_feature_function in enumerate(self.
            dynamic_feature_functions):
            self._obs_array[self._idx, self._nb_static_features + i
                ] = dynamic_feature_function(self.historical_info)
        if self.windows is None:
            _step_index = self._idx
        else:
            _step_index = np.arange(self._idx + 1 - self.windows, self._idx + 1
                )
        return self._obs_array[_step_index]
    def reset(self, seed=None, options=None, **kwargs):
        super().reset(seed=seed, options=options, **kwargs)
        self._step = 0
        self._position = np.random.choice(self.positions
            ) if self.initial_position == 'random' else self.initial_position
        self._limit_orders = {}
        self._idx = 0
        if self.windows is not None:
            self._idx = self.windows - 1
        if self.max_episode_duration != 'max':
            self._idx = np.random.randint(low=self._idx, high=len(self.df) -
                self.max_episode_duration - self._idx)
        self._portfolio = TargetPortfolio(position=self._position, value=
            self.portfolio_initial_value, price=self._get_price())
        self.historical_info = History(max_size=len(self.df))
        self.historical_info.set(idx=self._idx, step=self._step, date=self.
            df.index.values[self._idx], position_index=self.positions.index
            (self._position), position=self._position, real_position=self.
            _position, data=dict(zip(self._info_columns, self._info_array[
            self._idx])), portfolio_valuation=self.portfolio_initial_value,
            portfolio_distribution=self._portfolio.
            get_portfolio_distribution(), reward=0)
        return self._get_obs(), self.historical_info[0]
    def render(self):
        pass
    def _trade(self, position, price=None):
        self._portfolio.trade_to_position(position, price=self._get_price() if
            price is None else price, trading_fees=self.trading_fees)
        self._position = position
        return
    def _take_action(self, position):
        if position != self._position:
            self._trade(position)
    def _take_action_order_limit(self):
        if len(self._limit_orders) > 0:
            ticker = self._get_ticker()
            for position, params in self._limit_orders.items():
                if position != self._position and params['limit'] <= ticker[
                    'high'] and params['limit'] >= ticker['low']:
                    self._trade(position, price=params['limit'])
                    if not params['persistent']:
                        del self._limit_orders[position]
    def add_limit_order(self, position, limit, persistent=False):
        self._limit_orders[position] = {'limit': limit, 'persistent':
            persistent}
    def step(self, position_index=None):
        if position_index is not None:
            self._take_action(self.positions[position_index])
        self._idx += 1
        self._step += 1
        self._take_action_order_limit()
        price = self._get_price()
        self._portfolio.update_interest(borrow_interest_rate=self.
            borrow_interest_rate)
        portfolio_value = self._portfolio.valorisation(price)
        portfolio_distribution = self._portfolio.get_portfolio_distribution()
        done, truncated = False, False
        if portfolio_value <= 0:
            done = True
        if self._idx >= len(self.df) - 1:
            truncated = True
        if isinstance(self.max_episode_duration, int
            ) and self._step >= self.max_episode_duration - 1:
            truncated = True
        self.historical_info.add(idx=self._idx, step=self._step, date=self.
            df.index.values[self._idx], position_index=position_index,
            position=self._position, real_position=self._portfolio.
            real_position(price), data=dict(zip(self._info_columns, self.
            _info_array[self._idx])), portfolio_valuation=portfolio_value,
            portfolio_distribution=portfolio_distribution, reward=0)
        if not done:
            reward = self.reward_function(self.historical_info)
            self.historical_info['reward', -1] = reward
        if done or truncated:
            self.calculate_metrics()
            self.log()
        return self._get_obs(), self.historical_info['reward', -1
            ], done, truncated, self.historical_info[-1]
    def add_metric(self, name, function):
        self.log_metrics.append({'name': name, 'function': function})
    def calculate_metrics(self):
        self.results_metrics = {'Market Return':
            f"{100 * (self.historical_info['data_close', -1] / self.historical_info['data_close', 0] - 1):5.2f}%"
            , 'Portfolio Return':
            f"{100 * (self.historical_info['portfolio_valuation', -1] / self.historical_info['portfolio_valuation', 0] - 1):5.2f}%"
            }
        for metric in self.log_metrics:
            self.results_metrics[metric['name']] = metric['function'](self.
                historical_info)
    def get_metrics(self):
        return self.results_metrics
    def log(self):
        if self.verbose > 0:
            text = ''
            for key, value in self.results_metrics.items():
                text += f'{key} : {value}   |   '
            print(text)
    def save_for_render(self, dir='render_logs'):
        assert 'open' in self.df and 'high' in self.df and 'low' in self.df and 'close' in self.df, 'Your DataFrame needs to contain columns : open, high, low, close to render !'
        columns = list(set(self.historical_info.columns) - set([
            f'date_{col}' for col in self._info_columns]))
        history_df = pd.DataFrame(self.historical_info[columns], columns=
            columns)
        history_df.set_index('date', inplace=True)
        history_df.sort_index(inplace=True)
        render_df = self.df.join(history_df, how='inner')
        if not os.path.exists(dir):
            os.makedirs(dir)
        render_df.to_pickle(
            f"{dir}/{self.name}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl"
            )
class MultiDatasetTradingEnv(TradingEnv):
    def __init__(self, dataset_dir, *args, preprocess=lambda df: df,
        episodes_between_dataset_switch=1, **kwargs):
        self.dataset_dir = dataset_dir
        self.preprocess = preprocess
        self.episodes_between_dataset_switch = episodes_between_dataset_switch
        self.dataset_pathes = glob.glob(self.dataset_dir)
        if len(self.dataset_pathes) == 0:
            raise FileNotFoundError(
                f'No dataset found with the path : {self.dataset_dir}')
        self.dataset_nb_uses = np.zeros(shape=(len(self.dataset_pathes),))
        super().__init__(self.next_dataset(), *args, **kwargs)
    def next_dataset(self):
        self._episodes_on_this_dataset = 0
        potential_dataset_pathes = np.where(self.dataset_nb_uses == self.
            dataset_nb_uses.min())[0]
        random_int = np.random.randint(potential_dataset_pathes.size)
        dataset_idx = potential_dataset_pathes[random_int]
        dataset_path = self.dataset_pathes[dataset_idx]
        self.dataset_nb_uses[dataset_idx] += 1
        self.name = Path(dataset_path).name
        return self.preprocess(pd.read_pickle(dataset_path))
    def reset(self, seed=None, options=None, **kwargs):
        self._episodes_on_this_dataset += 1
        if (self._episodes_on_this_dataset % self.
            episodes_between_dataset_switch == 0):
            self._set_df(self.next_dataset())
        if self.verbose > 1:
            print(f'Selected dataset {self.name} ...')
        return super().reset(seed=seed, options=options, **kwargs)
class TradingEnvV2(TradingEnv):
    def __init__(self, df: pd.DataFrame, positions: list=[0, 1],
        dynamic_feature_functions=[dynamic_feature_last_position_taken,
        dynamic_feature_real_position], reward_function=
        basic_reward_function, windows=None, trading_fees=0,
        borrow_interest_rate=0, portfolio_initial_value=1000,
        initial_position='random', max_episode_duration='max', verbose=1,
        name='Stock', render_mode='logs', session_aware=True, base_spread=
        0.0001, news_manager=None, avoid_news_levels=['high']):
        self.session_aware = session_aware
        self.base_spread = base_spread
        self.news_manager = news_manager
        self.avoid_news_levels = avoid_news_levels
        if session_aware:
            self.session_manager = SessionManager()
        else:
            self.session_manager = None
        if news_manager is not None:
            df = news_manager.filter_trading_data(df, impact_levels=
                avoid_news_levels)
        super().__init__(df=df, positions=positions,
            dynamic_feature_functions=dynamic_feature_functions,
            reward_function=reward_function, windows=windows, trading_fees=
            trading_fees, borrow_interest_rate=borrow_interest_rate,
            portfolio_initial_value=portfolio_initial_value,
            initial_position=initial_position, max_episode_duration=
            max_episode_duration, verbose=verbose, name=name, render_mode=
            render_mode)
    def _get_current_timestamp(self) ->pd.Timestamp:
        return pd.Timestamp(self.df.index.values[self._idx])
    def _get_dynamic_spread(self) ->float:
        if not self.session_aware or self.session_manager is None:
            return self.base_spread
        current_time = self._get_current_timestamp()
        return self.session_manager.get_current_spread(current_time, self.
            base_spread)
    def _get_dynamic_trading_fees(self) ->float:
        if not self.session_aware:
            return self.trading_fees
        dynamic_spread = self._get_dynamic_spread()
        return max(self.trading_fees, dynamic_spread)
    def _should_avoid_trading(self) ->bool:
        if self.news_manager is None:
            return False
        current_time = self._get_current_timestamp()
        return self.news_manager.should_avoid_trading(current_time, self.
            avoid_news_levels)
    def _trade(self, position, price=None):
        if self._should_avoid_trading():
            return
        dynamic_fees = self._get_dynamic_trading_fees()
        self._portfolio.trade_to_position(position, price=self._get_price() if
            price is None else price, trading_fees=dynamic_fees)
        self._position = position
        return
    def _get_session_features(self) ->dict:
        if not self.session_aware or self.session_manager is None:
            return {}
        current_time = self._get_current_timestamp()
        session_info = self.session_manager.get_session_info(current_time)
        features = {}
        features['session_spread_multiplier'] = session_info[
            'spread_multiplier']
        features['session_high_volatility'] = int(session_info[
            'high_volatility'])
        features['session_london_ny_overlap'] = int(session_info['session'] ==
            'london_ny_overlap')
        features['session_asian'] = int(session_info['session'] == 'asian')
        features['session_london'] = int(session_info['session'] == 'london')
        features['session_new_york'] = int(session_info['session'] ==
            'new_york')
        return features
    def _get_news_features(self) ->dict:
        if self.news_manager is None:
            return {}
        current_time = self._get_current_timestamp()
        features = {}
        features['avoid_high_impact'] = int(self.news_manager.
            should_avoid_trading(current_time, ['high']))
        features['avoid_moderate_impact'] = int(self.news_manager.
            should_avoid_trading(current_time, ['moderate']))
        next_news = self.news_manager.get_next_news_event(current_time, [
            'high', 'moderate'])
        features['next_news_minutes'] = next_news['minutes_until'
            ] if next_news else 999
        features['next_news_high_impact'] = int(next_news['impact_level'] ==
            'high' if next_news else False)
        return features
    def step(self, position_index=None):
        if position_index is not None and not self._should_avoid_trading():
            self._take_action(self.positions[position_index])
        self._idx += 1
        self._step += 1
        self._take_action_order_limit()
        price = self._get_price()
        self._portfolio.update_interest(borrow_interest_rate=self.
            borrow_interest_rate)
        portfolio_value = self._portfolio.valorisation(price)
        portfolio_distribution = self._portfolio.get_portfolio_distribution()
        done, truncated = False, False
        if portfolio_value <= 0:
            done = True
        if self._idx >= len(self.df) - 1:
            truncated = True
        if isinstance(self.max_episode_duration, int
            ) and self._step >= self.max_episode_duration - 1:
            truncated = True
        info_dict = dict(zip(self._info_columns, self._info_array[self._idx]))
        session_features = self._get_session_features()
        news_features = self._get_news_features()
        info_dict.update(session_features)
        info_dict.update(news_features)
        self.historical_info.add(idx=self._idx, step=self._step, date=self.
            df.index.values[self._idx], position_index=position_index,
            position=self._position, real_position=self._portfolio.
            real_position(price), data=info_dict, portfolio_valuation=
            portfolio_value, portfolio_distribution=portfolio_distribution,
            reward=0)
        if not done:
            reward = self.reward_function(self.historical_info)
            self.historical_info['reward', -1] = reward
        if done or truncated:
            self.calculate_metrics()
            self.log()
        return self._get_obs(), self.historical_info['reward', -1
            ], done, truncated, self.historical_info[-1]
    def add_session_metric(self, name: str, function):
        self.add_metric(name, function)
    def get_session_stats(self):
        if not self.session_aware:
            return {}
        session_data = []
        for i in range(len(self.historical_info)):
            try:
                session_info = self.historical_info[i].get('data', {})
                session_data.append({'session_spread_multiplier':
                    session_info.get('session_spread_multiplier', 1.0),
                    'session_high_volatility': session_info.get(
                    'session_high_volatility', 0), 'portfolio_return': (
                    self.historical_info['portfolio_valuation', i] / self.
                    historical_info['portfolio_valuation', 0] - 1) * 100})
            except:
                continue
        if not session_data:
            return {}
        df_sessions = pd.DataFrame(session_data)
        return {'avg_spread_multiplier': df_sessions[
            'session_spread_multiplier'].mean(), 'high_volatility_periods':
            df_sessions['session_high_volatility'].sum(),
            'avg_return_high_vol': df_sessions[df_sessions[
            'session_high_volatility'] == 1]['portfolio_return'].mean(),
            'avg_return_low_vol': df_sessions[df_sessions[
            'session_high_volatility'] == 0]['portfolio_return'].mean()}