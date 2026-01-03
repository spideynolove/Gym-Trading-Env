from __future__ import annotations

from gymnasium.envs.registration import register


def register_env(id: str, entry_point: str):
    register(id=id, entry_point=entry_point, disable_env_checker=True, order_enforce=False)


register_env(id="TradingEnv-v1", entry_point="gym_trading_env.environments:TradingEnv")
register_env(
    id="TradingEnv-v2", entry_point="gym_trading_env.environments:TradingEnvV2"
)
register_env(
    id="MultiDatasetTradingEnv",
    entry_point="gym_trading_env.environments:MultiDatasetTradingEnv",
)
