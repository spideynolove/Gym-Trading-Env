from typing import Dict, Any
class Portfolio:
    def __init__(self, asset: float, fiat: float, interest_asset: float=0.0,
        interest_fiat: float=0.0):
        self.asset = asset
        self.fiat = fiat
        self.interest_asset = interest_asset
        self.interest_fiat = interest_fiat
    def valorisation(self, price: float) ->float:
        return (self.asset * price + self.fiat - self.interest_asset *
            price - self.interest_fiat)
    def real_position(self, price: float) ->float:
        net_asset_value = (self.asset - self.interest_asset) * price
        total_value = self.valorisation(price)
        return net_asset_value / total_value if total_value != 0 else 0.0
    def position(self, price: float) ->float:
        asset_value = self.asset * price
        total_value = self.valorisation(price)
        return asset_value / total_value if total_value != 0 else 0.0
    def trade_to_position(self, target_position: float, price: float,
        trading_fees: float) ->None:
        current_position = self.position(price)
        interest_reduction_ratio = 1.0
        if target_position <= 0 and current_position < 0:
            interest_reduction_ratio = min(1.0, target_position /
                current_position)
        elif target_position >= 1 and current_position > 1:
            interest_reduction_ratio = min(1.0, (target_position - 1) / (
                current_position - 1))
        if interest_reduction_ratio < 1.0:
            self.asset -= (1 - interest_reduction_ratio) * self.interest_asset
            self.fiat -= (1 - interest_reduction_ratio) * self.interest_fiat
            self.interest_asset *= interest_reduction_ratio
            self.interest_fiat *= interest_reduction_ratio
        target_asset_amount = target_position * self.valorisation(price
            ) / price
        asset_trade = target_asset_amount - self.asset
        if asset_trade > 0:
            asset_trade = asset_trade / (1 - trading_fees + trading_fees *
                target_position)
            asset_fiat = -asset_trade * price
            self.asset += asset_trade * (1 - trading_fees)
            self.fiat += asset_fiat
        else:
            asset_trade = asset_trade / (1 - trading_fees * target_position)
            asset_fiat = -asset_trade * price
            self.asset += asset_trade
            self.fiat += asset_fiat * (1 - trading_fees)
    def update_interest(self, borrow_interest_rate: float) ->None:
        self.interest_asset = max(0.0, -self.asset) * borrow_interest_rate
        self.interest_fiat = max(0.0, -self.fiat) * borrow_interest_rate
    def __str__(self) ->str:
        return f'{self.__class__.__name__}({self.__dict__})'
    def describe(self, price: float) ->None:
        print(
            f'Value: {self.valorisation(price)}, Position: {self.position(price)}'
            )
    def get_portfolio_distribution(self) ->Dict[str, float]:
        return {'asset': max(0, self.asset), 'fiat': max(0, self.fiat),
            'borrowed_asset': max(0, -self.asset), 'borrowed_fiat': max(0, 
            -self.fiat), 'interest_asset': self.interest_asset,
            'interest_fiat': self.interest_fiat}
class TargetPortfolio(Portfolio):
    def __init__(self, position: float, value: float, price: float):
        super().__init__(asset=position * value / price, fiat=(1 - position
            ) * value, interest_asset=0.0, interest_fiat=0.0)