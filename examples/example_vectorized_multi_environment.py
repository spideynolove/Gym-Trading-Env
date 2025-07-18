import sys
sys.path.append('./src')
import pandas as pd
import numpy as np
import gymnasium as gym
import datetime
import gym_trading_env
from gym_trading_env.downloader import download
def add_features(df: pd.DataFrame):
    df['feature_close'] = df['close'].pct_change()
    df['feature_open'] = df['open'] / df['close']
    df['feature_high'] = df['high'] / df['close']
    df['feature_low'] = df['low'] / df['close']
    df['feature_volume'] = df['volume'] / df['volume'].rolling(7 * 24).max()
    df.dropna(inplace=True)
    return df
def reward_function(history):
    return np.log(history['portfolio_valuation', -1] / history[
        'portfolio_valuation', -2])
if __name__ == '__main__':
    env = gym.make_vec(id='MultiDatasetTradingEnv', num_envs=3, dataset_dir
        ='examples/data/*.pkl', preprocess=add_features, windows=5,
        positions=[-1, -0.5, 0, 0.5, 1, 1.5, 2], initial_position=0,
        trading_fees=0.01 / 100, borrow_interest_rate=0.0003 / 100,
        reward_function=reward_function, portfolio_initial_value=1000)
    observation, info = env.reset()
    while True:
        actions = [1, 2, 3]
        observation, reward, done, truncated, info = env.step(actions)