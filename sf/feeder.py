import pandas as pd
from datetime import datetime
import time
import threading
import queue
from .processors import DataProcessor

class RealTimeOHLCVFeeder:
    def __init__(self, data_file, speed_multiplier=100, delimiter='\t', has_header=False, 
                 column_order=None, timestamp_format='%Y-%m-%d %H:%M'):
        self.data_file = data_file
        self.delimiter = delimiter
        self.has_header = has_header
        self.column_order = column_order or ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        self.timestamp_format = timestamp_format
        self.speed_multiplier = speed_multiplier
        
        self.raw_data = []
        self.current_index = -1
        self.running = False
        self.data_processor = DataProcessor()

        self.feature_config = None
        self.cached_features = None
        self.last_processed_index = -1

        self.timestamps = []
        self.opens = []
        self.highs = []
        self.lows = []
        self.closes = []
        self.volumes = []
        
        self.processed_df = pd.DataFrame()
        self.data_queue = queue.Queue()
        
        self._load_all_data()
    
    def _load_all_data(self):
        try:
            with open(self.data_file, 'r') as f:
                if self.has_header:
                    next(f)
                for line in f:
                    bar_data = self.parse_data_line(line)
                    if bar_data:
                        self.raw_data.append(bar_data)
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def parse_data_line(self, line):
        parts = line.strip().split(self.delimiter)
        if len(parts) != len(self.column_order):
            return None
        try:
            record = {}
            for i, col in enumerate(self.column_order):
                if col == 'timestamp':
                    record['timestamp'] = datetime.strptime(parts[i], self.timestamp_format)
                elif col == 'volume':
                    record['volume'] = int(parts[i])
                else:
                    record[col] = float(parts[i])
            return record
        except:
            return None
    
    def get_next_bar(self):
        if self.current_index + 1 >= len(self.raw_data):
            return None
        
        self.current_index += 1
        bar = self.raw_data[self.current_index]
        
        self.timestamps.append(bar['timestamp'])
        self.opens.append(bar['open'])
        self.highs.append(bar['high'])
        self.lows.append(bar['low'])
        self.closes.append(bar['close'])
        self.volumes.append(bar['volume'])
        
        self._update_processed_data()
        
        return bar
    
    def _update_processed_data(self):
        if len(self.closes) < 2:
            return
        
        current_df = pd.DataFrame({
            'timestamp': self.timestamps,
            'open': self.opens,
            'high': self.highs,
            'low': self.lows,
            'close': self.closes,
            'volume': self.volumes
        })
        
        self.processed_df = current_df.copy()
    
    def get_current_state(self):
        if self.current_index < 0:
            return None
        
        return {
            'current_bar': {
                'timestamp': self.timestamps[self.current_index],
                'open': self.opens[self.current_index],
                'high': self.highs[self.current_index],
                'low': self.lows[self.current_index],
                'close': self.closes[self.current_index],
                'volume': self.volumes[self.current_index]
            },
            'historical_data': {
                'timestamps': self.timestamps.copy(),
                'opens': self.opens.copy(),
                'highs': self.highs.copy(),
                'lows': self.lows.copy(),
                'closes': self.closes.copy(),
                'volumes': self.volumes.copy()
            },
            'processed_data': self.processed_df.copy() if not self.processed_df.empty else pd.DataFrame(),
            'current_index': self.current_index,
            'total_bars': len(self.raw_data)
        }
    
    def get_lookback_window(self, window_size=50):
        if self.current_index < 0:
            return None
        
        start_idx = max(0, self.current_index - window_size + 1)
        end_idx = self.current_index + 1
        
        return {
            'timestamps': self.timestamps[start_idx:end_idx],
            'opens': self.opens[start_idx:end_idx],
            'highs': self.highs[start_idx:end_idx],
            'lows': self.lows[start_idx:end_idx],
            'closes': self.closes[start_idx:end_idx],
            'volumes': self.volumes[start_idx:end_idx],
            'window_start_index': start_idx,
            'window_end_index': end_idx - 1
        }
    
    def has_next_bar(self):
        return self.current_index + 1 < len(self.raw_data)
    
    def reset(self):
        self.current_index = -1
        self.timestamps = []
        self.opens = []
        self.highs = []
        self.lows = []
        self.closes = []
        self.volumes = []
        self.processed_df = pd.DataFrame()
        self.cached_features = None
        self.last_processed_index = -1

    def simulate_trading_session(self, callback_func=None):
        self.running = True
        while self.running and self.has_next_bar():
            bar = self.get_next_bar()
            if bar is None:
                break
            
            if callback_func:
                callback_func(self.get_current_state())
            
            time.sleep(3600 / self.speed_multiplier / 1000)
        
        self.running = False
    
    def start_async_simulation(self, callback_func):
        def simulation_thread():
            self.simulate_trading_session(callback_func)
        
        thread = threading.Thread(target=simulation_thread, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        self.running = False
    
    def is_ready(self):
        return len(self.raw_data) > 0
    
    def get_total_bars(self):
        return len(self.raw_data)

    def set_feature_config(self, config_path=None, config_dict=None):
        if config_path:
            self.data_processor = DataProcessor(config_path)
            self.feature_config = config_path
        elif config_dict:
            self.data_processor.config = config_dict
            self.feature_config = config_dict

    def get_current_features(self, window_size=50, add_patterns=True, add_volatility=True, add_time_features=True, add_categorical=True):
        if self.current_index < 0 or len(self.closes) < max(window_size, 30):
            return {}
        
        if self.last_processed_index == self.current_index and self.cached_features is not None:
            return self.cached_features
        
        lookback_data = self.get_lookback_window(window_size)
        if not lookback_data:
            return {}
        
        window_df = pd.DataFrame({
            'timestamp': lookback_data['timestamps'],
            'open': lookback_data['opens'],
            'high': lookback_data['highs'],
            'low': lookback_data['lows'],
            'close': lookback_data['closes'],
            'volume': lookback_data['volumes']
        })
        
        try:
            features_df = self.data_processor.process_dataframe(
                window_df,
                add_patterns=add_patterns,
                add_volatility=add_volatility,
                add_time_features=add_time_features,
                add_categorical=add_categorical
            )
            
            latest_features = {}
            for col in features_df.columns:
                if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
                    value = features_df[col].iloc[-1]
                    if pd.notna(value):
                        latest_features[f'feature_{col}'] = value
            
            self.cached_features = latest_features
            self.last_processed_index = self.current_index
            return latest_features
            
        except Exception as e:
            print(f"Error in feature processing: {e}")
            return {}

    def get_enhanced_state(self, window_size=50, **feature_kwargs):
        base_state = self.get_current_state()
        if base_state is None:
            return None
        
        features = self.get_current_features(window_size, **feature_kwargs)
        base_state['features'] = features
        return base_state