import sys
sys.path.append('./src')
from gym_trading_env.downloader import download, EXCHANGE_LIMIT_RATES
import datetime
EXCHANGE_LIMIT_RATES['bybit'] = {'limit': 200, 'pause_every': 120, 'pause': 2}
download(exchange_names=['bybit'], symbols=['BTC/USDT', 'ETH/USDT'],
    timeframe='1h', dir='examples/data', since=datetime.datetime(year=2023,
    month=1, day=1))