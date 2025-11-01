import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import datetime
EXCHANGE_LIMIT_RATES = {
    'bitfinex2': {
        'limit': 10000, 'pause_every': 1, 'pause': 3},
    'binance': {
        'limit': 1000, 'pause_every': 10, 'pause': 1},
    'huobi': {
        'limit': 1000, 'pause_every': 10, 'pause': 1}
}


async def _ohlcv(
    exchange: ccxt.Exchange, symbol: str, timeframe: str,
        limit: int, step_since: int, timedelta: int
) -> pd.DataFrame:
    result = await exchange.fetch_ohlcv(
        symbol=symbol, timeframe=timeframe,
        limit=limit, since=step_since
    )
    df = pd.DataFrame(result, columns=[
        'timestamp_open', 'open', 'high', 'low', 'close', 'volume'
    ])
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df['date_open'] = pd.to_datetime(df['timestamp_open'], unit='ms')
    df['date_close'] = pd.to_datetime(
        df['timestamp_open'] + timedelta, unit='ms')
    return df


async def _download_symbol(
    exchange: ccxt.Exchange, symbol: str,
    timeframe: str = '5m', since: int = None,
    until: int = None, limit: int = 1000,
        pause_every: int = 10, pause: float = 1.0
) -> pd.DataFrame:
    if since is None:
        since = int(datetime.datetime(2020, 1, 1).timestamp() * 1000)
    if until is None:
        until = int(datetime.datetime.now().timestamp() * 1000)
    timedelta_ms = int(pd.Timedelta(timeframe).total_seconds() * 1000)
    tasks = []
    results = []
    for step_since in range(since, until, limit * timedelta_ms):
        tasks.append(
            _ohlcv(exchange, symbol, timeframe, limit,
                   step_since, timedelta_ms)
        )
        if len(tasks) >= pause_every:
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            await asyncio.sleep(pause)
            tasks = []
    if tasks:
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    final_df = pd.concat(results, ignore_index=True)
    final_df = final_df[
        (final_df['timestamp_open'] > since)
        & (final_df['timestamp_open'] < until)
    ]
    final_df.drop(columns=['timestamp_open'], inplace=True)
    final_df.set_index('date_open', drop=True, inplace=True)
    final_df.sort_index(inplace=True)
    final_df.dropna(inplace=True)
    final_df.drop_duplicates(inplace=True)
    return final_df


async def _download_symbols(exchange_name: str, symbols: list, dir: str,
                            timeframe: str, **kwargs):
    exchange = getattr(ccxt, exchange_name)({'enableRateLimit': True})
    try:
        for symbol in symbols:
            df = await _download_symbol(exchange, symbol=symbol, timeframe=timeframe, **kwargs)
            filepath = (
                f"{dir}/{exchange_name}-{symbol.replace('/', '')}-{timeframe}.pkl"
            )
            df.to_pickle(filepath)
            print(f'{symbol} downloaded from {exchange_name}, stored at {filepath}')
    finally:
        await exchange.close()


async def _download(exchange_names: list, symbols: list,
                    timeframe: str, dir: str, since: datetime.datetime,
                    until: datetime.datetime = None):
    if until is None:
        until = datetime.datetime.now()
    since_ms = int(since.timestamp() * 1000)
    until_ms = int(until.timestamp() * 1000)
    tasks = []
    for exchange_name in exchange_names:
        config = EXCHANGE_LIMIT_RATES[exchange_name]
        task = _download_symbols(exchange_name=exchange_name, symbols=symbols,
                                 timeframe=timeframe, dir=dir, limit=config['limit'],
                                 pause_every=config['pause_every'], pause=config['pause'],
                                 since=since_ms, until=until_ms)
        tasks.append(task)
    await asyncio.gather(*tasks)


def download(*args, **kwargs):
    asyncio.run(_download(*args, **kwargs))


async def main():
    await _download(exchange_names=['binance', 'bitfinex2', 'huobi'],
                    symbols=['BTC/USDT', 'ETH/USDT'], timeframe='30m',
                    dir='test/data', since=datetime.datetime(2019, 1, 1))
if __name__ == '__main__':
    asyncio.run(main())
