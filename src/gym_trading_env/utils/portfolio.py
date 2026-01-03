from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(slots=True)
class Portfolio:
    asset: float
    fiat: float
    interest_asset: float = 0.0
    interest_fiat: float = 0.0

    def valorisation(self, price: float) -> float:
        return (
            self.asset * price
            + self.fiat
            - self.interest_asset * price
            - self.interest_fiat
        )

    def real_position(self, price: float) -> float:
        net_asset_value = (self.asset - self.interest_asset) * price
        total_value = self.valorisation(price)
        return net_asset_value / total_value if total_value != 0 else 0.0

    def position(self, price: float) -> float:
        asset_value = self.asset * price
        total_value = self.valorisation(price)
        return asset_value / total_value if total_value != 0 else 0.0

    def trade_to_position(
        self, target_position: float, price: float, trading_fees: float
    ):
        current_position = self.position(price)
        interest_reduction_ratio = self._get_interest_reduction_ratio(
            target_position, current_position
        )

        if interest_reduction_ratio < 1.0:
            self._reduce_interest(interest_reduction_ratio)

        target_asset_amount = target_position * self.valorisation(price) / price
        asset_trade = target_asset_amount - self.asset

        if asset_trade > 0:
            self._execute_buy(asset_trade, price, trading_fees, target_position)
        else:
            self._execute_sell(asset_trade, price, trading_fees, target_position)

    def _get_interest_reduction_ratio(
        self, target_position: float, current_position: float
    ) -> float:
        if target_position <= 0 and current_position < 0:
            return min(1.0, target_position / current_position)
        if target_position >= 1 and current_position > 1:
            return min(1.0, (target_position - 1) / (current_position - 1))
        return 1.0

    def _reduce_interest(self, ratio: float):
        self.asset -= (1 - ratio) * self.interest_asset
        self.fiat -= (1 - ratio) * self.interest_fiat
        self.interest_asset *= ratio
        self.interest_fiat *= ratio

    def _execute_buy(
        self, asset_trade: float, price: float, trading_fees: float, target_position: float
    ):
        asset_trade /= 1 - trading_fees + trading_fees * target_position
        asset_fiat = -asset_trade * price
        self.asset += asset_trade * (1 - trading_fees)
        self.fiat += asset_fiat

    def _execute_sell(
        self, asset_trade: float, price: float, trading_fees: float, target_position: float
    ):
        asset_trade /= 1 - trading_fees * target_position
        asset_fiat = -asset_trade * price
        self.asset += asset_trade
        self.fiat += asset_fiat * (1 - trading_fees)

    def update_interest(self, borrow_interest_rate: float):
        self.interest_asset = max(0.0, -self.asset) * borrow_interest_rate
        self.interest_fiat = max(0.0, -self.fiat) * borrow_interest_rate

    def describe(self, price: float):
        print(f"Value: {self.valorisation(price)}, Position: {self.position(price)}")

    def get_portfolio_distribution(self) -> Dict[str, float]:
        return {
            "asset": max(0, self.asset),
            "fiat": max(0, self.fiat),
            "borrowed_asset": max(0, -self.asset),
            "borrowed_fiat": max(0, -self.fiat),
            "interest_asset": self.interest_asset,
            "interest_fiat": self.interest_fiat,
        }


@dataclass(slots=True)
class TargetPortfolio(Portfolio):
    position: float
    value: float
    price: float

    def __post_init__(self):
        self.asset = self.position * self.value / self.price
        self.fiat = (1 - self.position) * self.value
        self.interest_asset = 0.0
        self.interest_fiat = 0.0
