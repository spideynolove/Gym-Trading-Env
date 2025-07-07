import pandas as pd
import numpy as np
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import datetime
import pytz

class AssetType(Enum):
    FOREX = "forex"
    COMMODITIES = "commodities"
    BONDS = "bonds"
    EQUITIES = "equities"

@dataclass
class AssetDataset:
    asset_type: AssetType
    symbol: str
    data: pd.DataFrame
    path: str
    last_updated: datetime.datetime

class IntermarketDatasetManager:
    
    def __init__(self):
        self.asset_datasets = {}
        self.correlation_matrix = {}
        self.synchronized_data = None
        self.forex_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'USDCHF']
        self.commodities = ['XAUUSD', 'WTIUSD', 'CRB_INDEX']
        self.bonds = ['US10Y', 'DE10Y', 'UK10Y', 'CA10Y', 'AU10Y', 'JP10Y']
        self.equities = ['SPX', 'DAX', 'FTSE', 'NIKKEI', 'ASX', 'TSX']
    
    def load_multi_asset_datasets(self, base_dir: str, preprocess_func=None):
        asset_patterns = {
            AssetType.FOREX: f"{base_dir}/forex/*.pkl",
            AssetType.COMMODITIES: f"{base_dir}/commodities/*.pkl", 
            AssetType.BONDS: f"{base_dir}/bonds/*.pkl",
            AssetType.EQUITIES: f"{base_dir}/equities/*.pkl"
        }
        
        for asset_type, pattern in asset_patterns.items():
            files = glob.glob(pattern)
            for file_path in files:
                symbol = Path(file_path).stem
                try:
                    data = pd.read_pickle(file_path)
                    if preprocess_func:
                        data = preprocess_func(data)
                    
                    dataset = AssetDataset(
                        asset_type=asset_type,
                        symbol=symbol,
                        data=data,
                        path=file_path,
                        last_updated=datetime.datetime.now(pytz.UTC)
                    )
                    self.asset_datasets[f"{asset_type.value}_{symbol}"] = dataset
                except Exception as e:
                    print(f"Failed to load {file_path}: {e}")
    
    def synchronize_datasets(self, reference_timeframe='1H'):
        if not self.asset_datasets:
            return None
        
        all_indices = []
        for dataset in self.asset_datasets.values():
            all_indices.append(dataset.data.index)
        
        common_index = all_indices[0]
        for idx in all_indices[1:]:
            common_index = common_index.intersection(idx)
        
        synchronized_datasets = {}
        for key, dataset in self.asset_datasets.items():
            sync_data = dataset.data.loc[common_index].copy()
            synchronized_datasets[key] = sync_data
        
        self.synchronized_data = synchronized_datasets
        return synchronized_datasets
    
    def get_asset_data(self, asset_type: AssetType, symbol: str = None):
        if symbol:
            key = f"{asset_type.value}_{symbol}"
            return self.asset_datasets.get(key)
        else:
            return {k: v for k, v in self.asset_datasets.items() 
                   if v.asset_type == asset_type}
    
    def calculate_intermarket_correlations(self, window=60):
        if not self.synchronized_data:
            self.synchronize_datasets()
        
        correlation_data = {}
        for key, data in self.synchronized_data.items():
            if 'close' in data.columns:
                correlation_data[key] = data['close'].pct_change()
        
        correlation_df = pd.DataFrame(correlation_data)
        rolling_corr = correlation_df.rolling(window=window).corr()
        
        return rolling_corr
    
    def get_murphy_principle_data(self):
        principles_data = {}
        
        # Principle 1: Bonds vs Commodities inverse relationship
        bonds_data = self.get_asset_data(AssetType.BONDS)
        commodities_data = self.get_asset_data(AssetType.COMMODITIES)
        
        if bonds_data and commodities_data:
            us10y = bonds_data.get('bonds_US10Y')
            crb = commodities_data.get('commodities_CRB_INDEX')
            if us10y and crb:
                principles_data['bonds_commodities'] = {
                    'bonds': us10y.data['close'],
                    'commodities': crb.data['close']
                }
        
        # Principle 2: Bonds lead Equities  
        equities_data = self.get_asset_data(AssetType.EQUITIES)
        if bonds_data and equities_data:
            us10y = bonds_data.get('bonds_US10Y')
            spx = equities_data.get('equities_SPX')
            if us10y and spx:
                principles_data['bonds_equities'] = {
                    'bonds': us10y.data['close'],
                    'equities': spx.data['close']
                }
        
        # Principle 3: Commodities vs Currencies (inverse relationship)
        forex_data = self.get_asset_data(AssetType.FOREX)
        if commodities_data and forex_data:
            gold = commodities_data.get('commodities_XAUUSD')
            eurusd = forex_data.get('forex_EURUSD')
            if gold and eurusd:
                principles_data['commodities_currencies'] = {
                    'gold': gold.data['close'],
                    'usd_index': 1/eurusd.data['close']  # Approximate USD strength
                }
        
        # Principle 4: Currency strength tied to interest rate differentials
        if bonds_data and forex_data:
            us10y = bonds_data.get('bonds_US10Y')
            ca10y = bonds_data.get('bonds_CA10Y')
            usdcad = forex_data.get('forex_USDCAD')
            
            if us10y and ca10y and usdcad:
                principles_data['interest_rate_differentials'] = {
                    'us_yield': us10y.data['close'],
                    'ca_yield': ca10y.data['close'],
                    'usdcad': usdcad.data['close']
                }
        
        # Principle 5: Cross-market confirmation
        if equities_data and forex_data:
            eurjpy = forex_data.get('forex_EURJPY')
            nasdaq = equities_data.get('equities_NASDAQ')
            
            if eurjpy and nasdaq:
                principles_data['cross_market_confirmation'] = {
                    'eurjpy': eurjpy.data['close'],
                    'nasdaq': nasdaq.data['close']
                }
        
        return principles_data
    
    def get_bond_yield_spreads(self):
        bonds_data = self.get_asset_data(AssetType.BONDS)
        spreads = {}
        
        if bonds_data:
            us10y = bonds_data.get('bonds_US10Y')
            ca10y = bonds_data.get('bonds_CA10Y') 
            uk10y = bonds_data.get('bonds_UK10Y')
            de10y = bonds_data.get('bonds_DE10Y')
            
            if us10y and ca10y:
                spreads['US_CA_10Y'] = us10y.data['close'] - ca10y.data['close']
            if us10y and uk10y:
                spreads['US_UK_10Y'] = us10y.data['close'] - uk10y.data['close'] 
            if us10y and de10y:
                spreads['US_DE_10Y'] = us10y.data['close'] - de10y.data['close']
        
        return spreads
    
    def get_commodity_currency_pairs(self):
        forex_data = self.get_asset_data(AssetType.FOREX)
        commodities_data = self.get_asset_data(AssetType.COMMODITIES)
        
        pairs = {}
        
        if forex_data and commodities_data:
            # CAD/Oil relationship
            usdcad = forex_data.get('forex_USDCAD')
            oil = commodities_data.get('commodities_WTIUSD')
            if usdcad and oil:
                pairs['CAD_OIL'] = {
                    'currency': 1/usdcad.data['close'],  # CAD strength
                    'commodity': oil.data['close']
                }
            
            # AUD/Gold relationship  
            audusd = forex_data.get('forex_AUDUSD')
            gold = commodities_data.get('commodities_XAUUSD')
            if audusd and gold:
                pairs['AUD_GOLD'] = {
                    'currency': audusd.data['close'],
                    'commodity': gold.data['close']
                }
        
        return pairs
    
    def detect_correlation_regime_changes(self, threshold=0.3):
        correlations = self.calculate_intermarket_correlations()
        regime_changes = {}
        
        # Key relationships to monitor
        key_pairs = [
            ('forex_EURUSD', 'commodities_XAUUSD'),
            ('bonds_US10Y', 'equities_SPX'),
            ('forex_USDCAD', 'commodities_WTIUSD')
        ]
        
        for pair1, pair2 in key_pairs:
            if pair1 in correlations.columns and pair2 in correlations.columns:
                corr_series = correlations[pair1][pair2].dropna()
                if len(corr_series) > 1:
                    corr_change = corr_series.diff().abs()
                    regime_changes[f"{pair1}_{pair2}"] = corr_change > threshold
        
        return regime_changes
    
    def get_intermarket_signals(self, timestamp: datetime.datetime):
        if not self.synchronized_data:
            return {}
        
        signals = {}
        
        # Murphy Principle signals
        murphy_data = self.get_murphy_principle_data()
        
        # Bond-Commodity inverse signal
        if 'bonds_commodities' in murphy_data:
            bonds = murphy_data['bonds_commodities']['bonds']
            commodities = murphy_data['bonds_commodities']['commodities']
            
            # Calculate recent correlation
            recent_data = pd.DataFrame({
                'bonds': bonds.tail(20),
                'commodities': commodities.tail(20)
            }).pct_change().dropna()
            
            if len(recent_data) > 5:
                correlation = recent_data['bonds'].corr(recent_data['commodities'])
                signals['bonds_commodities_inverse'] = correlation < -0.5
        
        # Bond yield spread signals
        spreads = self.get_bond_yield_spreads()
        for spread_name, spread_data in spreads.items():
            if len(spread_data) > 20:
                recent_spread = spread_data.tail(20)
                spread_trend = (recent_spread.iloc[-1] - recent_spread.iloc[-5]) / recent_spread.iloc[-5]
                signals[f"{spread_name}_trend"] = spread_trend
        
        return signals